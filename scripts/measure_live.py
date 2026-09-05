#!/usr/bin/env python3
"""Read live counters over a bounded steady-state window; no repeated-frame FPS."""
import argparse,json,time,urllib.request
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--url',default='http://127.0.0.1:8080')
p.add_argument('--seconds',type=int,default=35)
p.add_argument('--output',required=True)
a=p.parse_args()
rows=[]
start=time.monotonic()
while time.monotonic()-start<a.seconds:
 try:
  with urllib.request.urlopen(a.url+'/stats.json',timeout=3) as r:s=json.load(r)
  if s['uptime_s']>5: rows.append(s)
 except Exception as e: print(type(e).__name__,flush=True)
 time.sleep(1)
if len(rows)<10:raise RuntimeError('Insufficient live samples')
f,l=rows[0],rows[-1];dt=l['uptime_s']-f['uptime_s']
if dt<=0:raise RuntimeError('Service restarted during measurement')
summary={'seconds':dt,'models':l['models'],'tracking':l['tracking']['enabled'],'rates':{}}
for name in ['capture','detect','depth']:
 summary['rates'][name]=(l[name]['frames']-f[name]['frames'])/dt
summary['rates']['composed']=(l['composed_frames']-f['composed_frames'])/dt
summary['rates']['encoded']=(l['encoded_frames']-f['encoded_frames'])/dt
for name in ['bpu','cpu']:
 vals=sorted(x[name]['util_pct'] for x in rows)
 summary[name]={'avg':sum(vals)/len(vals),'p95':vals[int((len(vals)-1)*.95)],'max':vals[-1]}
summary['depth_age_ms_max']=max(x['depth']['age_ms'] for x in rows)
path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps({'summary':summary,'samples':rows},indent=2)+'\n')
print(json.dumps(summary,indent=2))
