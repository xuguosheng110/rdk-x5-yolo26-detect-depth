#!/usr/bin/env python3
"""Compare C++ deployment outputs to pinned official Python wrappers on bus.jpg."""
import json,sys
from pathlib import Path
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'vendor/rdk_model_zoo'
sys.path.insert(0,str(V))
sys.path.insert(0,str(V/'samples/vision/ultralytics_yolo26/runtime/python'))
sys.path.insert(0,str(V/'samples/vision/yolo26_depth/runtime/python'))
from yolo26_det import YOLO26Detect,YOLO26Config
from yolo26_depth import Yolo26Depth
cv2.setNumThreads(1)
folder=ROOT/'reports/verify_quality'
img=cv2.imread(str(ROOT/'assets/bus.jpg'))
det=YOLO26Detect(YOLO26Config(model_path=str(ROOT/'models/yolo26s_detect_bayese_640x640_nv12.bin'),nms_thres=.45))
boxes,scores,classes=det.predict(img)
cpp=np.array(json.loads((folder/'detections.json').read_text()))
def iou(a,b):
 wh=np.maximum(0,np.minimum(a[2:4],b[2:4])-np.maximum(a[:2],b[:2]))
 inter=np.prod(wh)
 return inter/(np.prod(a[2:4]-a[:2])+np.prod(b[2:4]-b[:2])-inter+1e-9)
match=[]
for box,score,cls in zip(boxes,scores,classes):
 if score<.5:continue
 candidates=[x for x in cpp if int(x[5])==cls]
 match.append(max([iou(box,x) for x in candidates],default=0))
depth=Yolo26Depth(ROOT/'models/yolo26s_depth_bayese_768x768_nv12.bin').infer(img)
x=np.fromfile(folder/'log_depth.f32',np.float32).reshape(depth.log_depth.shape)
y=depth.log_depth
relative=np.abs(np.exp(x-y)-1)
report={'detection_count_cpp':len(cpp),'detection_count_official':len(boxes),
        'high_confidence_matching_iou':match,
        'log_depth_cosine':float(np.dot(x.ravel(),y.ravel())/(np.linalg.norm(x)*np.linalg.norm(y))),
        'depth_relative_median_error':float(np.median(relative)),
        'depth_relative_p95_error':float(np.percentile(relative,95)),
        'note':'Same official models; optimized libyuv bilinear versus official OpenCV preprocessing. This is numerical agreement on one image, not a dataset accuracy claim.'}
report['passed']=bool(match and min(match)>.95 and np.isfinite(x).all() and report['depth_relative_median_error']<.03 and report['depth_relative_p95_error']<.10)
(folder/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if not report['passed']:sys.exit(1)
