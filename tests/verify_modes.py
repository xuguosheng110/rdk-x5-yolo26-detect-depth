#!/usr/bin/env python3
"""Hardware acceptance: actual results, serialized switches and invalid input."""
import argparse,json,time,urllib.request,urllib.error
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8080');a=p.parse_args()
def get():
 with urllib.request.urlopen(a.url+'/api/status',timeout=3) as r:return json.load(r)
def post(body,origin=None):
 headers={'Content-Type':'application/json'}
 if origin:headers['Origin']=origin
 req=urllib.request.Request(a.url+'/api/mode',data=json.dumps(body).encode(),headers=headers)
 try:
  with urllib.request.urlopen(req,timeout=5) as r:return r.status
 except urllib.error.HTTPError as e:return e.code
assert post({'mode':'invalid'})==400
assert post({'mode':'yolo'},'https://unrelated.invalid')==403
results=[]
for mode in ['stereo','body','yolo','stereo','body','yolo']:
 t=time.monotonic();before=get()['generation'];assert post({'mode':mode})==202
 assert post({'mode':mode})==409,'simultaneous switch not rejected'
 while time.monotonic()-t<45:
  s=get()
  if s['mode']==mode and s['phase']=='ready' and s['generation']!=before:break
  time.sleep(.5)
 else:raise AssertionError(s)
 with urllib.request.urlopen(a.url+'/frame.jpg',timeout=4) as r:assert r.read(2)==b'\xff\xd8'
 metrics=s['metrics'];first=metrics.get('encoded_frames',metrics.get('frames',0));time.sleep(2)
 metrics=get()['metrics'];assert metrics.get('encoded_frames',metrics.get('frames',0))>first,'stale image'
 if mode=='body':assert metrics['ai_updates']>0
 if mode=='yolo':assert metrics['detect']['frames']>0 and metrics['depth']['frames']>0
 results.append({'mode':mode,'switch_s':round(time.monotonic()-t-2,2),'live':True})
 print(json.dumps(results[-1]),flush=True)
print(json.dumps({'passed':True,'switches':results}),flush=True)
