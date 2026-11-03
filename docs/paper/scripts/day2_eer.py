import pickle,numpy as np,json,sys
sys.path.insert(0,'.')
from engine import Template, decide
from sim import eer
S=pickle.load(open('../data/day2_S.pkl','rb')); n=len(S)
R={}
# Protocol A: template first 68 enrol windows (~36 s), genuine = enrol windows 74..113, impostor = other sessions' windows 74..113 (same span)
TA=[Template(s['E'][:68]) for s in S]
H=[s['E'][74:] for s in S]
gA=np.concatenate([TA[i].score(H[i]) for i in range(n)])
iA=np.concatenate([TA[i].score(H[j]) for i in range(n) for j in range(n) if i!=j])
e=eer(gA,iA); auc=float((gA[:,None]>iA[None,:]).mean())
R['A']=dict(eer=float(e[0]),thr=float(e[1]),auc=auc,ng=len(gA),ni=len(iA),far015=float((iA>=0.15).mean()),frr015=float((gA<0.15).mean()),far025=float((iA>=0.25).mean()),frr025=float((gA<0.25).mean()),far010=float((iA>=0.10).mean()),frr010=float((gA<0.10).mean()))
pu=[eer(TA[i].score(H[i]),np.concatenate([TA[i].score(H[j]) for j in range(n) if j!=i]))[0] for i in range(n)]
R['A']['per_user']=[float(x) for x in pu]
# Protocol B: full 114-window template, genuine = post-enrolment windows before first warning; impostor = other sessions' all enrol windows
gB=np.concatenate([S[i]['T'].score(S[i]['X'][S[i]['pre']]) for i in range(n)])
iB=np.concatenate([S[i]['T'].score(S[j]['E']) for i in range(n) for j in range(n) if i!=j])
e=eer(gB,iB); R['B']=dict(eer=float(e[0]),thr=float(e[1]),auc=float((gB[:,None]>iB[None,::3]).mean()),ng=len(gB),ni=len(iB),frr015=float((gB<0.15).mean()),far015=float((iB>=0.15).mean()))
# bootstrap CI over sessions for A
rng=np.random.default_rng(3); bs=[]
for b in range(500):
    idx=rng.integers(0,n,n)
    g=np.concatenate([TA[i].score(H[i]) for i in idx]); im=np.concatenate([TA[i].score(H[j]) for i in idx for j in range(n) if j!=i])
    bs.append(eer(g,im)[0])
R['A']['ci']=[float(np.percentile(bs,2.5)),float(np.percentile(bs,97.5))]
# feature-group ablation on A
for name,m in [('dynamics',np.arange(10)),('geometry',np.arange(10,16))]:
    g=np.concatenate([TA[i].score(H[i],mask=m) for i in range(n)]); im=np.concatenate([TA[i].score(H[j],mask=m) for i in range(n) for j in range(n) if j!=i])
    R['A']['eer_'+name]=float(eer(g,im)[0])
# Trace-driven handover replay: genuine holdout (40 windows=20 s) then impostor j's holdout windows; presets
P={'Strict':(0.25,4),'Balanced':(0.15,6),'Relaxed':(0.10,8)}
R['replay']={}
for name,(th,k) in P.items():
    det=0;lat=[];fl=0;trials=0
    for i in range(n):
        idx,_=decide(TA[i].score(H[i]),threshold=th,k=k)
        fl+= idx is not None
        for j in range(n):
            if j==i: continue
            sc=np.r_[TA[i].score(H[i]),TA[i].score(H[j])]
            idx,_=decide(sc,threshold=th,k=k); trials+=1
            if idx is not None and idx>=len(H[i]): det+=1; lat.append((idx-len(H[i])+1)*0.5)
    R['replay'][name]=dict(th=th,k=k,trials=trials,detected=det,lat_mean=float(np.mean(lat)),lat_p95=float(np.percentile(lat,95)),false_lock_genuine=fl,genuine_streams=n,
        early_fl=trials-det-sum(1 for _ in [])) 
print(json.dumps(R,indent=1))
json.dump(R,open('../data/day2_eer.json','w'),indent=1)
np.savez('../data/day2_scores.npz',gA=gA,iA=iA,gB=gB,iB=iB)
