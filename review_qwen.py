"""Optional Ollama reviewer; sends only prompt and reply, never other ratings."""
import argparse,json,urllib.request,fcntl,time
from pathlib import Path
from common import ROOT,read,save,bind,digest

def call(endpoint,path,body=None):
 req=urllib.request.Request(endpoint.rstrip('/')+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=900) as r:return json.load(r)
def payload(spec,row):
 return dict(model=spec['model'],messages=[dict(role='system',content=spec['rubric']),dict(role='user',content=json.dumps(dict(conversation=row['messages'],reply=row['text'])))],format=spec['schema'],stream=False,think=False,keep_alive='5m',options=spec['options'])
def validate(v):
 if type(v.get('target')) is not int or v['target'] not in [0,1,2]:raise ValueError('Invalid target')
 if type(v.get('coherence')) is not int or not 1<=v['coherence']<=5:raise ValueError('Invalid coherence')
 if type(v.get('unrelated')) is not bool:raise ValueError('Invalid issue flag')
 if not isinstance(v.get('evidence'),str) or not isinstance(v.get('reason'),str) or not v['reason'].strip():raise ValueError('Missing evidence/reason fields')
def run(a):
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 with (out/'lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  spec=read(ROOT/'protocols'/('guided-qwen.json' if a.guided else 'qwen-review-protocol.json'));rows=read(a.responses)['responses']
  bind(out/'manifest.json',dict(spec=spec,responses_sha256=digest(rows)))
  tags=call(a.endpoint,'/api/tags')['models']
  if not any(m['name']==spec['model'] and m['digest']==spec['digest'] for m in tags):raise ValueError('Expected pinned reviewer model is not installed')
  state=read(out/'state.json') if (out/'state.json').exists() else dict(ratings={})
  state.update(status='running',error=None)
  try:
   for row in sorted(rows,key=lambda r:digest(r['key'])):
    if (out/'pause').exists():state['status']='paused';break
    key=row['key']
    if key in state['ratings']:continue
    body=payload(spec,row);path=out/(key+'.json')
    if path.exists():
     artifact=read(path)
     if artifact['request']!=body:raise ValueError('Saved request mismatch')
     raw=artifact['response']
    else:
     start=time.time();raw=call(a.endpoint,'/api/chat',body);save(path,dict(request=body,response=raw,elapsed_seconds=time.time()-start))
    if raw.get('done_reason')=='length':raise ValueError('Truncated reviewer response')
    v=json.loads(raw['message']['content']);validate(v);v['evidence_valid']=not v['evidence'] or v['evidence'] in row['text'];state['ratings'][key]=v;save(out/'state.json',state)
   else:state['status']='complete'
  except Exception as exc:
   state.update(status='failed',error=str(exc));raise
  finally:save(out/'state.json',state)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--endpoint',default='http://127.0.0.1:11434');p.add_argument('--responses',default=str(ROOT/'results/followup-evidence.json'));p.add_argument('--out',default='runs/review');p.add_argument('--guided',action='store_true');run(p.parse_args())
