"""Native MLP intervention, extracted from the original Lab runtime."""
import contextlib,math

@contextlib.contextmanager
def steering(model,changes):
 handles=[]
 try:
  for c in changes:
   layer,neuron,offset=c['layer'],c['neuron'],c['offset']
   if type(layer) is not int or not 0<=layer<len(model.model.layers):raise ValueError('Invalid layer')
   projection=model.model.layers[layer].mlp.down_proj
   if type(neuron) is not int or not 0<=neuron<projection.in_features or not math.isfinite(offset):raise ValueError('Invalid neuron or offset')
   def hook(_module,args,index=neuron,delta=offset):
    x=args[0].clone();x[...,index]+=delta
    return (x,)+args[1:]
   if offset:handles.append(projection.register_forward_pre_hook(hook))
  yield
 finally:
  for handle in handles:handle.remove()

class Generator:
 def __init__(self,spec):
  import torch
  from transformers import AutoTokenizer,AutoModelForCausalLM
  torch.set_num_threads(4)
  torch.manual_seed(42)
  self.tok=AutoTokenizer.from_pretrained(spec['model'],revision=spec['revision'])
  self.model=AutoModelForCausalLM.from_pretrained(spec['model'],revision=spec['revision'],dtype=torch.bfloat16,attn_implementation='sdpa',device_map='cuda').eval()
 def generate(self,task,max_tokens):
  import torch
  ids=self.tok.apply_chat_template(task['messages'],tokenize=True,add_generation_prompt=True,enable_thinking=False,return_dict=False)
  x=torch.tensor([ids],device=self.model.device)
  with steering(self.model,task['changes']),torch.inference_mode():
   out=self.model.generate(input_ids=x,attention_mask=torch.ones_like(x),do_sample=False,max_new_tokens=max_tokens,pad_token_id=self.tok.eos_token_id)
  tokens=out[0,len(ids):].tolist()
  return dict(text=self.tok.decode(tokens,skip_special_tokens=True),tokens=len(tokens),at_token_limit=len(tokens)>=max_tokens)
