"""Checkpointed reproduction; never writes the original saved results."""
import argparse,fcntl,signal,platform,importlib.metadata
from pathlib import Path
from common import ROOT,read,save,bind,digest
from steer import Generator

def run(out,generator_factory=Generator):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 with (out/'lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  spec=read(ROOT/'protocols/followup-protocol.json');bind(out/'protocol.json',spec)
  state=read(out/'state.json') if (out/'state.json').exists() else dict(responses=[],status='ready',source='New reproduction, not original evidence')
  seen={r['key'] for r in state['responses']};stop=[False]
  if not (out/'environment.json').exists():
   versions={}
   for name in ['torch','transformers','accelerate']:
    try:versions[name]=importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:versions[name]='not installed'
   save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),packages=versions,decoding='greedy; no sampling',seed=42))
  def pause(*_):stop[0]=True
  signal.signal(signal.SIGINT,pause);signal.signal(signal.SIGTERM,pause)
  gen=None
  try:
   for task in spec['tasks']:
    if stop[0] or (out/'pause').exists():state['status']='paused';break
    if task['key'] in seen:continue
    if gen is None:gen=generator_factory(spec)
    state['status']='running';save(out/'state.json',state)
    state['responses'].append({**task,**gen.generate(task,spec['max_new_tokens'])});save(out/'state.json',state)
   else:state['status']='complete'
  except Exception as exc:state.update(status='failed',error=str(exc));raise
  finally:save(out/'state.json',state)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',default='runs/followup');a=p.parse_args();run(a.out)
