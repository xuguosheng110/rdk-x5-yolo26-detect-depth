#!/usr/bin/env python3
"""ROS images/results to atomic latest-frame files; no camera ownership."""
import argparse, array, json, os, time, struct
from collections import deque
from pathlib import Path
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from ai_msgs.msg import PerceptionTargets

cv2.setNumThreads(1)
OUT = Path('/run/rdk-vision')

def atomic(name, data):
    p = OUT / name
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_bytes(data)
    os.replace(tmp, p)

def decode(m):
    a = np.frombuffer(m.data, np.uint8)
    if m.encoding == 'nv12':
        return cv2.cvtColor(a.reshape(m.height * 3 // 2, m.width), cv2.COLOR_YUV2BGR_NV12)
    if m.encoding in ('bgr8', 'rgb8'):
        a = a.reshape(m.height, m.step)[:, :m.width * 3].reshape(m.height, m.width, 3)
        return cv2.cvtColor(a, cv2.COLOR_RGB2BGR) if m.encoding == 'rgb8' else a
    raise ValueError('Unsupported encoding: ' + m.encoding)

class Bridge(Node):
    def __init__(self, mode):
        super().__init__('rdk_display_bridge')
        self.mode = mode
        self.auto = mode == "auto"
        self.config = Path(__file__).resolve().parents[1]/"config/selected-mode.env"
        self.left = None
        self.rgb_frames=deque(maxlen=16)
        self.targets = None
        self.age_targets = {}
        self.target_time = 0
        self.ai_updates = 0
        self.frames = 0
        self.start = time.monotonic()
        self.last = 0
        self.pub = self.create_publisher(Image, '/rdk/image_raw', 10)
        self.create_subscription(Image, '/image_left_raw', self.camera, qos_profile_sensor_data)
        if mode in ('stereo','auto'):
            self.create_subscription(Image, '/StereoNetNode/stereonet_depth', self.stereo, qos_profile_sensor_data)
        if mode in ('body','auto'):
            self.create_subscription(PerceptionTargets, '/hobot_mono2d_body_detection', self.ai, 10)
            self.create_subscription(PerceptionTargets, '/hobot_face_age_detection', self.age, 10)
        OUT.mkdir(exist_ok=True)

    def save(self, frame, ages=None):
        ok, jpg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
        if not ok: return
        self.frames += 1
        atomic('display.jpg', jpg.tobytes())
        atomic('bridge.json', json.dumps({'mode': self.mode, 'frames': self.frames,
            'updated': time.time(), 'fps': self.frames / max(.1, time.monotonic()-self.start),
            'ages': ages or [], 'ai_updates': self.ai_updates, 'ai_age_s': time.monotonic()-self.target_time}).encode())

    def camera(self, m):
        now = time.monotonic()
        if self.auto:
            try: mode=self.config.read_text().strip().partition('=')[2]
            except OSError: mode='yolo'
            if mode != self.mode:
                self.mode=mode; self.frames=0; self.start=now
                self.targets=None; self.age_targets={}; self.ai_updates=0; self.target_time=0
        if now - self.last < 1/15: return
        self.last = now
        try:
            full=decode(m)
            if self.mode=="stereo":
                self.rgb_frames.append((m.header.stamp.sec+m.header.stamp.nanosec*1e-9,full))
                atomic('camera.json', json.dumps({'updated':time.time(),'width':m.width,'height':m.height}).encode())
                return
            frame = cv2.resize(full, (640,544))
        except (ValueError, cv2.error) as e:
            self.get_logger().error(str(e)); return
        self.left = frame
        ok, jpg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if ok: atomic('left.jpg', jpg.tobytes())
        atomic('camera.json', json.dumps({'updated': time.time(), 'width': m.width, 'height': m.height}).encode())
        if self.mode == 'body':
            frame = cv2.copyMakeBorder(frame,0,0,160,160,cv2.BORDER_CONSTANT,value=(114,114,114))
            # Preserve the same timestamp for body boxes and the age ROI join.
            yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV_I420).reshape(-1)
            n = 960*544
            nv12 = np.empty(n*3//2, np.uint8)
            nv12[:n] = yuv[:n]
            nv12[n::2] = yuv[n:n+n//4]
            nv12[n+1::2] = yuv[n+n//4:]
            msg = Image(); msg.header = m.header
            msg.width=960; msg.height=544; msg.encoding='nv12'; msg.step=960; msg.data=array.array('B', nv12.tobytes())
            self.pub.publish(msg)
            ages = []
            if self.targets is not None and now - self.target_time < 1:
                for t in self.targets.targets:
                    age_time, age = self.age_targets.get(t.track_id, (0, None))
                    if now - age_time > 1: age = None
                    if age is not None: ages.append(int(age))
                    for r in t.rois:
                        box=r.rect; x,y=int(box.x_offset),int(box.y_offset)
                        color=(60,220,120) if r.type=='face' else (240,180,50)
                        cv2.rectangle(frame,(x,y),(x+int(box.width),y+int(box.height)),color,2)
                        label=r.type + (f' ~{int(age)}y' if r.type=='face' and age is not None else '')
                        for attr in t.attributes:
                            if attr.type != 'age': label += f' {attr.type}:{attr.value}'
                        cv2.putText(frame,label,(x,max(20,y-5)),cv2.FONT_HERSHEY_SIMPLEX,.55,color,2)
                    for group in t.points:
                        for i, point in enumerate(group.point):
                            if len(group.confidence)>i and group.confidence[i]<.2: continue
                            cv2.circle(frame,(int(point.x),int(point.y)),3,(60,220,120),-1)
                        if group.type=='body_kps' and len(group.point)>=17:
                            for a,b in ((5,6),(5,7),(7,9),(6,8),(8,10),(5,11),(6,12),(11,12),(11,13),(13,15),(12,14),(14,16)):
                                if len(group.confidence)>max(a,b) and min(group.confidence[a],group.confidence[b])<.2: continue
                                pa,pb=group.point[a],group.point[b]
                                cv2.line(frame,(int(pa.x),int(pa.y)),(int(pb.x),int(pb.y)),(80,210,255),2)
            self.save(frame[:,160:800], ages)

    def ai(self, msg):
        self.targets=msg; self.target_time=time.monotonic(); self.ai_updates += 1

    def age(self, msg):
        now=time.monotonic()
        self.age_targets={t.track_id:(now,a.value) for t in msg.targets for a in t.attributes if a.type=='age'}

    def stereo(self,m):
        if self.mode!='stereo' or not self.rgb_frames: return
        try:
            endian='>' if m.is_bigendian else '<'
            if m.encoding in ('mono16','16UC1'):
                depth=np.frombuffer(m.data,dtype=endian+'u2').reshape(m.height,m.step//2)[:,:m.width].astype(np.float32)*.001
            elif m.encoding=='32FC1':
                depth=np.frombuffer(m.data,dtype=endian+'f4').reshape(m.height,m.step//4)[:,:m.width]
            else: raise ValueError('Unsupported depth encoding: '+m.encoding)
            valid=np.isfinite(depth)&(depth>0)
            # Rank inverse depth like the official adaptive disparity palette.
            inverse=np.zeros_like(depth);np.divide(1.,depth,out=inverse,where=valid)
            gray=np.zeros(depth.shape,np.uint8)
            if np.count_nonzero(valid)>1:
                knots=np.percentile(inverse[valid],[0,10,50,90,100])
                if knots[-1]-knots[0]>1e-6:
                    gray[valid]=np.interp(inverse[valid],knots,[0,64,128,192,255]).astype(np.uint8)
            color=cv2.applyColorMap(gray,cv2.COLORMAP_JET);color[~valid]=0
            stamp=m.header.stamp.sec+m.header.stamp.nanosec*1e-9
            rgb_stamp,rgb=min(self.rgb_frames,key=lambda item:abs(item[0]-stamp))
            if abs(rgb_stamp-stamp)>.5: return
            grid=[]
            for row in range(3):
                for col in range(4):
                    x,y=(col+.5)/4,(row+.5)/3
                    value=float(depth[min(m.height-1,int(y*m.height)),min(m.width-1,int(x*m.width))])
                    grid.append({'x':x,'y':y,'meters':round(value,2) if np.isfinite(value) and value>0 else None})
            meta={'rgb_width':rgb.shape[1],'rgb_height':rgb.shape[0],
                  'depth_width':m.width,'depth_height':m.height,'grid':grid,
                  'stamp':stamp,'rgb_delta_ms':round(abs(rgb_stamp-stamp)*1000,1)}
            ok1,j1=cv2.imencode('.jpg',rgb,[cv2.IMWRITE_JPEG_QUALITY,92])
            ok2,j2=cv2.imencode('.jpg',color,[cv2.IMWRITE_JPEG_QUALITY,92])
            if not(ok1 and ok2): return
            header=json.dumps(meta).encode();rgb_bytes=j1.tobytes()
            atomic('stereo.frame',struct.pack('<II',len(header),len(rgb_bytes))+header+rgb_bytes+j2.tobytes())
            # Keep the existing snapshot API compatible; interactive clients use the HD bundle.
            self.save(np.vstack((cv2.resize(rgb,(m.width,m.height)),color)))
        except (ValueError,cv2.error) as e: self.get_logger().error(str(e))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--mode',choices=['yolo','stereo','body','auto'],required=True)
    a=p.parse_args(); rclpy.init(); node=Bridge(a.mode)
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally: node.destroy_node(); rclpy.try_shutdown()
