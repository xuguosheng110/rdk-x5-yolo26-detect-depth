#!/usr/bin/env python3
"""LAN/touch portal. One serialized systemd workload, persistent selected mode."""
import hashlib, json, os, subprocess, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
RUN=Path('/run/rdk-vision')
MODES={'yolo':'YOLO + 单目深度','stereo':'双目深度','body':'人体 + 年龄'}
lock=threading.Lock()
state={'mode':'yolo','phase':'starting','generation':time.time_ns(),'error':''}

def read_json(p):
    try:return json.loads(p.read_text())
    except (OSError,ValueError):return {}

def ui_revision():
    return hashlib.sha256((ROOT/"web/modes.html").read_bytes()).hexdigest()[:12]

def status():
    s=dict(state); s['ui_revision']=ui_revision(); camera=read_json(RUN/'camera.json')
    s['camera_ready']=time.time()-camera.get('updated',0)<3
    s['labels']=MODES
    if s['mode']=='yolo':
        try:
            with urllib.request.urlopen('http://127.0.0.1:8081/stats.json',timeout=.5) as r: metrics=json.load(r)
            s['metrics']=metrics
            ready=metrics.get('encoded_frames',0)>0 and s['camera_ready']
        except Exception:ready=False
    else:
        metrics=read_json(RUN/'bridge.json'); s['metrics']=metrics
        ready=metrics.get('mode')==s['mode'] and time.time()-metrics.get('updated',0)<3 and s['camera_ready']
    if s['mode']=='body':ready=ready and metrics.get('ai_updates',0)>0 and metrics.get('ai_age_s',999)<3
    if s['phase']!='switching':
        s['phase']='ready' if ready else 'waiting'
    return s

def switch(mode):
    if not lock.acquire(blocking=False):return False
    state.update(phase='switching',error='')
    def work():
        try:
            subprocess.run(['systemctl','stop','rdk-x5-mode'],check=True,timeout=20)
            for f in ('display.jpg','bridge.json','stereo.frame'):(RUN/f).unlink(missing_ok=True)
            config=ROOT/'config/selected-mode.env'
            tmp=config.with_suffix('.tmp'); tmp.write_text('RDK_MODE='+mode+'\n'); os.replace(tmp,config)
            state.update(mode=mode,generation=time.time_ns())
            subprocess.run(['systemctl','start','rdk-x5-mode'],check=True,timeout=15)
        except Exception as e:state['error']=str(e)
        finally:state['phase']='waiting'; lock.release()
    threading.Thread(target=work,daemon=True).start();return True

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,code,data,content='application/json'):
        if not isinstance(data,bytes):data=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type',content); self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store'); self.end_headers();self.wfile.write(data)
    def do_GET(self):
        path=urlsplit(self.path).path
        try:
            if path in ('/api/status','/stats.json'):return self.reply(200,status())
            if path=='/':return self.reply(200,(ROOT/'web/modes.html').read_bytes().replace(b'__UI_REVISION__',ui_revision().encode()),'text/html; charset=utf-8')
            if path=='/stereo.frame':
                if state['phase']=='switching' or state['mode']!='stereo':return self.reply(503,{'error':'switching'})
                return self.reply(200,(RUN/'stereo.frame').read_bytes(),'application/octet-stream')
            if path=='/frame.jpg':
                if state['phase']=='switching':return self.reply(503,{'error':'switching'})
                if state['mode']=='yolo':
                    with urllib.request.urlopen('http://127.0.0.1:8081/snapshot.jpg',timeout=2) as r:data=r.read()
                else:data=(RUN/'display.jpg').read_bytes()
                return self.reply(200,data,'image/jpeg')
            return self.reply(404,{'error':'not found'})
        except (OSError,ValueError):self.reply(503,{'error':'waiting for live frame'})
    def do_POST(self):
        if self.path!='/api/mode':return self.reply(404,{'error':'not found'})
        # Reject browser requests from another origin and non-JSON form submissions.
        origin=self.headers.get('Origin')
        if origin and urlsplit(origin).netloc!=self.headers.get('Host'):return self.reply(403,{'error':'origin'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.reply(415,{'error':'JSON required'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=256:raise ValueError()
            mode=json.loads(self.rfile.read(size)).get('mode')
            if mode not in MODES:raise ValueError()
        except (ValueError,TypeError,AttributeError):return self.reply(400,{'error':'invalid mode'})
        if not switch(mode):return self.reply(409,{'error':'switch in progress'})
        self.reply(202,{'mode':mode})

if __name__=='__main__':
    RUN.mkdir(exist_ok=True)
    config=ROOT/'config/selected-mode.env'
    if config.exists():
        mode=config.read_text().strip().partition('=')[2]
        if mode in MODES:state['mode']=mode
    ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
