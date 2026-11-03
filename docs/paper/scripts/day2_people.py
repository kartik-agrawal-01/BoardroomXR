import pickle,json,numpy as np,sys
sys.path.insert(0,'.')
from engine import Template
from sim import eer
from replay import replay
S=pickle.load(open('../data/day2_S.pkl','rb'))
order=json.load(open('../data/day2_session_order.json'))['order']
byf={s['f']:s for s in S}
SS=[byf[f] for f in order]          # chronological S01..S11
PERSON=['P01','P02','P03','P03','P01','P01','P04','P04','P03','P02','P02']
n=len(SS)
TT=[Template(s['E'][:68]) for s in SS]; H=[s['E'][74:] for s in SS]
same=lambda i,j: PERSON[i]==PERSON[j]
g=np.concatenate([TT[i].score(H[i]) for i in range(n)])
imp=np.concatenate([TT[i].score(H[j]) for i in range(n) for j in range(n) if not same(i,j)])
xs=np.concatenate([TT[i].score(H[j]) for i in range(n) for j in range(n) if i!=j and same(i,j)])
R={}
e=eer(g,imp); R['A_people']=dict(eer=float(e[0]),ng=len(g),ni=len(imp),auc=float((g[:,None]>imp[None,:]).mean()))
for nm,m in [('geo',np.arange(10,16)),('dyn',np.arange(10))]:
    gg=np.concatenate([TT[i].score(H[i],mask=m) for i in range(n)]); ii=np.concatenate([TT[i].score(H[j],mask=m) for i in range(n) for j in range(n) if not same(i,j)])
    xx=np.concatenate([TT[i].score(H[j],mask=m) for i in range(n) for j in range(n) if i!=j and same(i,j)])
    R['A_people_'+nm]=float(eer(gg,ii)[0]); R['xsess_'+nm+'_mean']=float(xx.mean()); R['imp_'+nm+'_mean']=float(ii.mean())
# same person, deliberately different session: how often accepted
R['xsess']=dict(n=len(xs),mean=float(xs.mean()),imp_mean=float(imp.mean()),gen_mean=float(g.mean()),
     frac_above_015=float((xs>=0.15).mean()),imp_above_015=float((imp>=0.15).mean()),gen_above_015=float((g>=0.15).mean()))
# EER treating same-person other sessions as genuine (person-level verification across deliberate change)
gx=np.concatenate([g,xs]); R['person_level_eer']=float(eer(gx,imp)[0])
# Interleaved protocol C people-level
blocks=np.arange(114)//20; C_tr=np.where(blocks%2==0)[0]; C_te=np.array([i for i in range(114) if blocks[i]%2==1 and i%20>=6])
TC=[Template(s['E'][C_tr]) for s in SS]
gc=np.concatenate([TC[i].score(SS[i]['E'][C_te]) for i in range(n)]); ic=np.concatenate([TC[i].score(SS[j]['E'][C_te]) for i in range(n) for j in range(n) if not same(i,j)])
R['C_people']=float(eer(gc,ic)[0])
# bootstrap by person
rng=np.random.default_rng(4); bs=[]
people=sorted(set(PERSON))
for b in range(500):
    pick=rng.choice(people,4)
    idx=[i for p in pick for i in range(n) if PERSON[i]==p]
    gb=np.concatenate([TT[i].score(H[i]) for i in idx]); ib=np.concatenate([TT[i].score(H[j]) for i in idx for j in range(n) if not same(i,j)])
    bs.append(eer(gb,ib)[0])
R['A_people']['ci']=[float(np.percentile(bs,2.5)),float(np.percentile(bs,97.5))]
# per-session pairwise matrix mean (chronological), person labels
M=np.array([[TT[i].score(H[j]).mean() for j in range(n)] for i in range(n)])
R['M_same_offdiag_mean']=float(np.mean([M[i,j] for i in range(n) for j in range(n) if i!=j and same(i,j)]))
R['M_diff_mean']=float(np.mean([M[i,j] for i in range(n) for j in range(n) if not same(i,j)]))
# replay restricted to different-person pairs
from engine import decide
PRE={'Strict':(0.25,4),'Balanced':(0.15,6),'Relaxed':(0.10,8)}
R['replay_people']={}
for mname,mask in [('all',None),('geo',np.arange(10,16))]:
  for name,(th,k) in PRE.items():
    fl=0;el=0;det=0;lat=[]
    for i in range(n):
        gi=TT[i].score(H[i],mask=mask); fl+=decide(gi,threshold=th,k=k)[0] is not None
        for j in range(n):
            if same(i,j): continue
            idx,_=decide(np.r_[gi,TT[i].score(H[j],mask=mask)],threshold=th,k=k)
            if idx is not None and idx<len(gi): continue
            el+=1
            if idx is not None: det+=1; lat.append((idx-len(gi)+1)*0.5)
    R['replay_people'][mname+'_'+name]=dict(fl=fl,n=n,el=el,det=det,lat=float(np.mean(lat)) if lat else None)
print(json.dumps(R,indent=1))
json.dump(dict(R=R,person=PERSON),open('../data/day2_people.json','w'),indent=1)
np.save('../data/day2_crossmatrix_chrono.npy',M)
