import math
def holm(pvalues):
 out=[1.]*len(pvalues);running=0.
 for rank,i in enumerate(sorted(range(len(pvalues)),key=lambda i:pvalues[i])):
  running=max(running,min(1.,pvalues[i]*(len(pvalues)-rank)));out[i]=running
 return out

def paired_binary_p(wins,losses):
    n=wins+losses
    return sum(math.comb(n,k) for k in range(wins,n+1))/(2**n) if n else 1.


def analyze(spec,responses,reviews):
    expected={t['key'] for t in spec['tasks']}
    if len(responses)!=448 or not expected.issubset(reviews):return dict(status='review pending',rated=sum(k in reviews for k in expected),required=448)
    rows={(r['phase'],r['prompt_index'],r['condition']):r for r in responses}
    units=[(f,i) for f in ['creature','object'] for i in range(32)]
    comparisons=[]
    positive=lambda r:reviews[r['key']]['target']==2
    for condition in spec['analysis']['comparators']:
        pairs=[(positive(rows[f,i,'candidate:1']),positive(rows[f,i,condition])) for f,i in units]
        wins=sum(a and not b for a,b in pairs);losses=sum(b and not a for a,b in pairs)
        comparisons.append(dict(condition=condition,wins=wins,losses=losses,ties=64-wins-losses,advantage=(wins-losses)/64,p_raw=paired_binary_p(wins,losses)))
    for r,p in zip(comparisons,holm([r['p_raw'] for r in comparisons])):r['p_adjusted']=p
    own=[rows[f,i,'candidate:1'] for f,i in units]
    quality=sum(reviews[r['key']]['coherence']>=4 and not reviews[r['key']]['unrelated'] and not r['at_token_limit'] for r in own)
    rates=[]
    for condition in ['baseline','candidate:1','candidate:-1','random-0:1','random-0:-1','random-1:1','random-1:-1']:
        for family in ['all','creature','object']:
            selected=[rows[f,i,condition] for f,i in units if family=='all' or f==family]
            rates.append(dict(condition=condition,family=family,clearly_small=sum(positive(r) for r in selected),n=len(selected)))
    passed=quality>=58 and all(r['p_adjusted']<=.05 and r['advantage']>=.15 for r in comparisons)
    return dict(status='passes this reviewed object/creature bank' if passed else 'did not meet all predefined criteria',reviewed_pass=passed,quality=quality,comparisons=comparisons,rates=rates,rated=448,required=448)
