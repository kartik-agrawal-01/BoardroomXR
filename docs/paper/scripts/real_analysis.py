import numpy as np, json
from engine import Template, decide
D=np.load('../data/real_windows.npz')
P={k[2:]:D[k] for k in D.files if k.startswith('P_')}
keys=sorted(P); lab={k:f'V{i+1}' for i,k in enumerate(keys)}
res={'per_person':{}}
gen_all,imp_all=[],[]
for k in keys:
    F=P[k]; n=len(F); ntr=max(5,int(round(0.6*n)))
    if n-ntr<2: continue
    tpl=Template(F[:ntr]); g=tpl.score(F[ntr:])
    im=np.concatenate([tpl.score(P[o]) for o in keys if o!=k])
    gen_all+=list(g); imp_all+=list(im)
    res['per_person'][lab[k]]={'windows':int(n),'train':int(ntr),'gen_mean':float(g.mean()),'gen_min':float(g.min()),'imp_mean':float(im.mean()),'imp_max':float(im.max()),'n_imp':int(len(im))}
g=np.array(gen_all); im=np.array(imp_all)
ths=np.linspace(0,1,2001); far=np.array([(im>=t).mean() for t in ths]); frr=np.array([(g<t).mean() for t in ths])
i=np.argmin(np.abs(far-frr)); res['eer']=float((far[i]+frr[i])/2); res['eer_thr']=float(ths[i])
res['far_at_025']=float((im>=0.25).mean()); res['frr_at_025']=float((g<0.25).mean())
res['n_gen']=len(g); res['n_imp']=len(im)
# AUC
res['auc']=float((g[:,None]>im[None,:]).mean()+0.5*(g[:,None]==im[None,:]).mean())
# eye-height & reach per volunteer
res['geom']={lab[k]:{'eye_h':float(P[k][:,13].mean()),'reach':float(P[k][:,10].mean()),'span':float(P[k][:,15].mean()),'angvel':float(P[k][:,2].mean())} for k in keys}
# logged impostor stream (5 logins vs V2 template)
imp=D['imp']; res['login_impostor_raw']=imp[:,16].tolist()
json.dump(res,open('../data/real_pilot_results.json','w'),indent=1)
np.savez('../data/real_scores.npz',gen=g,imp=im)
print(json.dumps({k:v for k,v in res.items() if k!='login_impostor_raw'},indent=1))
