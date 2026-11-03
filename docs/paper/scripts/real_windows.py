import csv,glob,numpy as np,json
META=('t','state','raw_score','smoothed_score','violations')
def load(p):
    rows=[]
    with open(p,encoding='utf-8-sig',errors='replace') as f:
        lines=f.read().splitlines()
    if not lines: return [],None
    hdr=lines[0].split(','); names=[h for h in hdr if h not in META]
    for ln in lines[1:]:
        v=ln.split(',')
        if len(v)!=len(hdr): continue  # truncated last line
        try: rows.append({h:(x if h=='state' else float(x)) for h,x in zip(hdr,v)})
        except ValueError: continue
    return rows,names
people={}
for p in sorted(glob.glob('data/headset_logs/BiometricLogs/*enrol*.csv')):
    r,names=load(p)
    F=np.array([[x[n] for n in names] for x in r if x['state']=='Enrolling'])
    if len(F): people[p.split('_')[-2]+'_'+p.split('_')[-1][:6]]=F
imp=[]
for p in sorted(glob.glob('data/headset_logs/BiometricLogs/*verify*.csv')):
    r,names=load(p); imp+= [[x[n] for n in names]+[x['raw_score']] for x in r]
for k,F in people.items(): print(k,F.shape, np.round(F.mean(0)[[0,2,6,10,13,15]],3))
np.savez('data/real_windows.npz',names=np.array(names),imp=np.array(imp),**{('P_'+k):v for k,v in people.items()})
