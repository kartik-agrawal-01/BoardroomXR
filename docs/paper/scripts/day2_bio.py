import csv,glob,json,numpy as np,sys
sys.path.insert(0,'.')
from engine import Template, decide
from sim import eer
F=sorted(glob.glob('../data/day2/scores_*.csv'))
S=[]
for i,f in enumerate(F):
    r=list(csv.DictReader(open(f,encoding='utf-8-sig')))
    X=np.array([[float(x[k]) for k in list(r[0].keys())[5:]] for x in r])
    st=np.array([x['state'] for x in r]); t=np.array([float(x['t']) for x in r])
    raw=np.array([float(x['raw_score']) for x in r]); sm=np.array([float(x['smoothed_score']) for x in r])
    S.append(dict(f=f.split('/')[-1],X=X,st=st,t=t,raw=raw,sm=sm))
n=len(S)
for k,s in enumerate(S):
    E=s['X'][s['st']=='Enrolling']; s['E']=E
    post=np.where(s['st']!='Enrolling')[0]
    w=np.where(s['st']=='Warning')[0]; lo=np.where(s['st']=='LockedOut')[0]
    fw=w[0] if len(w) else None
    pre=[i for i in post if fw is None or i<fw]
    s['pre']=pre
    s['T']=Template(E)
    # check port reproduces device scores on post windows
    dev=np.abs(s['T'].score(s['X'][post])-s['raw'][post]).max()
    s['dev']=float(dev)
    s['lock']=bool(len(lo)); s['enrol_end']=float(s['t'][post[0]])
    s['t_lock_after_enrol']=float(s['t'][lo[0]]-s['t'][post[0]]) if len(lo) else None
    s['warn_to_lock']=float(s['t'][lo[0]]-s['t'][fw]) if len(lo) else None
    s['pre_mean']=float(s['raw'][pre].mean()) if pre else None
    print(k,s['f'][7:30],'E',len(E),'post',len(post),'pre',len(pre),'premean %.2f'%s['pre_mean'],'lock',s['lock'],s['t_lock_after_enrol'],s['warn_to_lock'],'portdev %.1e'%dev)
# cross matrix: template i vs enrol windows j (second half)
M=np.zeros((n,n))
for i in range(n):
    for j in range(n):
        M[i,j]=S[i]['T'].score(S[j]['E'][57:]).mean()
np.set_printoptions(precision=2,suppress=True,linewidth=200)
print(M)
np.save('../data/day2_crossmatrix.npy',M)
json.dump([{k:v for k,v in s.items() if k in('f','dev','lock','enrol_end','t_lock_after_enrol','warn_to_lock','pre_mean')}|{'n_pre':len(s['pre'])} for s in S],open('../data/day2_sessions.json','w'),indent=1)
import pickle; pickle.dump(S,open('../data/day2_S.pkl','wb'))
