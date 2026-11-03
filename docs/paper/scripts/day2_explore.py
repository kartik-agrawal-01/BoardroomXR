import pickle,numpy as np,sys
sys.path.insert(0,'.')
from engine import Template, ABS_FLOOR
from sim import eer
S=pickle.load(open('../data/day2_S.pkl','rb')); n=len(S)
def run(tr_idx,te_idx,score_fn,label,agg=1):
    g=[];im=[]
    for i in range(n):
        T=S[i]['E'][tr_idx]
        for j in range(n):
            sc=score_fn(T,S[j]['E'][te_idx])
            if agg>1: sc=np.convolve(sc,np.ones(agg)/agg,'valid')
            (g if i==j else im).append(sc)
    g=np.concatenate(g); im=np.concatenate(im)
    print('%-45s EER %.3f AUC %.3f'%(label,eer(g,im)[0],(g[:,None]>im[None,::2]).mean()))
base=lambda T,X: Template(T).score(X)
A_tr=np.arange(68); A_te=np.arange(74,114)
blocks=np.arange(114)//20
C_tr=np.where((blocks%2==0))[0]; C_te=np.array([i for i in range(114) if blocks[i]%2==1 and i%20>=6])
run(A_tr,A_te,base,'A deployed scorer (drift split)')
run(C_tr,C_te,base,'C deployed scorer (interleaved blocks)')
run(A_tr,A_te,base,'A + mean of 10 windows (5 s)',agg=10)
run(C_tr,C_te,base,'C + mean of 10 windows',agg=10)
geo=np.arange(10,16)
run(A_tr,A_te,lambda T,X: Template(T).score(X,mask=geo),'A geometry only')
run(C_tr,C_te,lambda T,X: Template(T).score(X,mask=geo),'C geometry only')
run(A_tr,A_te,lambda T,X: Template(T).score(X,mask=geo),'A geometry only, 5 s mean',agg=10)
# pilot-derived Fisher weights (independent data)
R=np.load('../data/real_windows.npz'); P=[R[k] for k in R.files if k.startswith('P_')]
within=np.mean([p.var(0) for p in P],0); between=np.var([p.mean(0) for p in P],0)
w=between/(within+1e-9); w=w/w.sum()*16
print('pilot fisher weights',np.round(w,2))
def wscore(T,X,w=w):
    t=Template(T); z=np.clip((X-t.mean)/t.sd,-6,6); return np.exp(-0.5*(w*z**2).mean(-1))
run(A_tr,A_te,wscore,'A pilot-Fisher-weighted')
run(C_tr,C_te,wscore,'C pilot-Fisher-weighted')
run(A_tr,A_te,wscore,'A pilot-Fisher-weighted, 5 s mean',agg=10)
print('--- cohort T-norm (cohort excludes claimed user AND the impostor)')
def tnorm_run(tr,te,mask,label,agg=1):
    TT=[Template(S[i]['E'][tr]) for i in range(n)]
    g=[];im=[]
    for i in range(n):
        for j in range(n):
            X=S[j]['E'][te]
            L=np.array([np.log(TT[c].score(X,mask=mask)+1e-12) for c in range(n)])
            coh=[c for c in range(n) if c!=i and c!=j]
            s=(L[i]-L[coh].mean(0))/(L[coh].std(0)+1e-6)
            if agg>1: s=np.convolve(s,np.ones(agg)/agg,'valid')
            (g if i==j else im).append(s)
    g=np.concatenate(g); im=np.concatenate(im)
    th=np.linspace(min(g.min(),im.min()),max(g.max(),im.max()),3000)
    far=np.array([(im>=t).mean() for t in th]); frr=np.array([(g<t).mean() for t in th]); k=np.argmin(abs(far-frr))
    print('%-45s EER %.3f'%(label,(far[k]+frr[k])/2))
tnorm_run(A_tr,A_te,None,'A T-norm all features')
tnorm_run(C_tr,C_te,None,'C T-norm all features')
tnorm_run(A_tr,A_te,geo,'A T-norm geometry')
tnorm_run(A_tr,A_te,None,'A T-norm all, 5 s mean',agg=10)
tnorm_run(C_tr,C_te,None,'C T-norm all, 5 s mean',agg=10)
