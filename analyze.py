"""Recompute published findings without a GPU or third-party packages."""
import argparse,json
from common import ROOT,read
from analysis_core import analyze

def ratings(name):
 if name=='codex':
  values=read(ROOT/'results/codex-ratings.json');inputs=read(ROOT/'results/codex-rating-inputs.json')
  return {r['key']:values[str(r['id'])] for r in inputs}
 names={'human':'human-ratings.json','qwen':'qwen-ratings.json','guided':'guided-qwen-ratings.json'}
 v=read(ROOT/'results'/names[name]);return v.get('reviews',v.get('ratings',v))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--reviewer',choices=['human','codex','qwen','guided'],default='human');p.add_argument('--responses',default=str(ROOT/'results/followup-evidence.json'));p.add_argument('--ratings',help='Custom rating map, keyed by task key');a=p.parse_args()
 custom=read(a.ratings) if a.ratings else None
 if custom is not None:custom=custom.get('reviews',custom.get('ratings',custom))
 result=analyze(read(ROOT/'protocols/followup-protocol.json'),read(a.responses)['responses'],custom if custom is not None else ratings(a.reviewer))
 if a.reviewer=='guided':result['interpretation']='Exploratory re-rating, not independent confirmation'
 print(json.dumps(result,indent=2))
