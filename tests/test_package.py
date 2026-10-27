import unittest,tempfile,json
from pathlib import Path
from common import ROOT,read,bind
from analysis_core import analyze,paired_binary_p,holm
from analyze import ratings
from review_qwen import payload,validate
from run_followup import run
class Tests(unittest.TestCase):
 def test_published_human_analysis_exact(self):
  got=analyze(read(ROOT/'protocols/followup-protocol.json'),read(ROOT/'results/followup-evidence.json')['responses'],ratings('human'))
  expected=read(ROOT/'results/human-condition-analysis.json')
  for key in ['quality','comparisons','rates','reviewed_pass']:self.assertEqual(got[key],expected[key])
 def test_ai_counts(self):
  for name,count in [('codex',35),('qwen',36),('guided',42)]:
   a=analyze(read(ROOT/'protocols/followup-protocol.json'),read(ROOT/'results/followup-evidence.json')['responses'],ratings(name))
   self.assertEqual(next(r['clearly_small'] for r in a['rates'] if r['condition']=='candidate:1' and r['family']=='all'),count)
 def test_statistics(self):
  self.assertEqual(paired_binary_p(0,0),1);self.assertEqual(paired_binary_p(3,0),.125);self.assertEqual(holm([.01,.04,.03]),[.03,.06,.06])
 def test_review_isolation(self):
  p=payload(read(ROOT/'protocols/guided-qwen.json'),dict(messages=[],text='hello',condition='SECRET',review={'target':2}))
  self.assertNotIn('SECRET',json.dumps(p));self.assertEqual(json.loads(p['messages'][1]['content']),dict(conversation=[],reply='hello'))
 def test_resume_and_pause(self):
  class Fake:
   calls=0
   def __init__(self,spec):pass
   def generate(self,task,max_tokens):Fake.calls+=1;return dict(text='test',tokens=1,at_token_limit=False)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'pause').touch();run(p,Fake);self.assertEqual(Fake.calls,0)
   (p/'pause').unlink();run(p,Fake);self.assertEqual(Fake.calls,448)
   run(p,Fake);self.assertEqual(Fake.calls,448)
   with self.assertRaises(ValueError):bind(p/'protocol.json',{})
 def test_hook_cleanup(self):
  try:import torch
  except ImportError:self.skipTest('Install GPU dependencies to exercise tensor hook')
  from types import SimpleNamespace
  from steer import steering
  layer=torch.nn.Linear(3,2,bias=False);layer.weight.data.fill_(1)
  model=SimpleNamespace(model=SimpleNamespace(layers=[SimpleNamespace(mlp=SimpleNamespace(down_proj=layer))]))
  x=torch.zeros(1,2,3)
  with self.assertRaises(RuntimeError):
   with steering(model,[dict(layer=0,neuron=1,offset=2)]):
    self.assertTrue(torch.equal(layer(x),torch.full((1,2,2),2.)));self.assertEqual(x.sum(),0);raise RuntimeError('test')
  self.assertEqual(len(layer._forward_pre_hooks),0);self.assertEqual(layer(x).sum(),0)
if __name__=='__main__':unittest.main()
