import pickle,json,numpy as np
from engine import Template
from sim import eer
S=pickle.load(open('../data/day2_S.pkl','rb'))
order=json.load(open('../data/day2_session_order.json'))['order']; byf={s['f']:s for s in S}
SS=[byf[f] for f in order]; PERSON=json.load(open('../data/day2_people.json'))['person']; n=len(SS)
same=lambda i,j: PERSON[i]==PERSON[j]
R={}
# B: deployed template vs post-enrol genuine windows / other persons' enrol windows
gB=np.concatenate([SS[i]['T'].score(SS[i]['X'][SS[i]['pre']]) for i in range(n)])
iB=np.concatenate([SS[i]['T'].score(SS[j]['E']) for i in range(n) for j in range(n) if not same(i,j)])
R['B']=dict(eer=float(eer(gB,iB)[0]),auc=float((gB[:,None]>iB[None,::3]).mean()),ng=len(gB))
blocks=np.arange(114)//20; C_tr=np.where(blocks%2==0)[0]; C_te=np.array([i for i in range(114) if blocks[i]%2==1 and i%20>=6])
TC=[Template(s['E'][C_tr]) for s in SS]
def agg(s,w): return np.convolve(s,np.ones(w)/w,'valid')
gc=[TC[i].score(SS[i]['E'][C_te]) for i in range(n)]
ic=[TC[i].score(SS[j]['E'][C_te]) for i in range(n) for j in range(n) if not same(i,j)]
R['C']=dict(eer=float(eer(np.concatenate(gc),np.concatenate(ic))[0]),auc=float((np.concatenate(gc)[:,None]>np.concatenate(ic)[None,:]).mean()))
R['C_avg5']=float(eer(np.concatenate([agg(x,10) for x in gc]),np.concatenate([agg(x,10) for x in ic]))[0])
TT=[Template(s['E'][:68]) for s in SS]; H=[s['E'][74:] for s in SS]
geo=np.arange(10,16)
gg=np.concatenate([TT[i].score(H[i],mask=geo) for i in range(n)]); ii=np.concatenate([TT[i].score(H[j],mask=geo) for i in range(n) for j in range(n) if not same(i,j)])
R['A_geo_auc']=float((gg[:,None]>ii[None,:]).mean())
pe=[eer(TT[i].score(H[i]),np.concatenate([TT[i].score(H[j]) for j in range(n) if not same(i,j)]))[0] for i in range(n)]
R['per_session']=[float(x) for x in pe]
print(json.dumps(R,indent=1)); json.dump(R,open('../data/day2_people2.json','w'),indent=1)
