import re,glob,os,json,csv,statistics as st
L=sorted(glob.glob('data/headset_logs/MFALogs/*.log'))
ev=[]
for f in L:
    for line in open(f,encoding='utf-8-sig',errors='replace'):
        if 'xrDiscover' in line: continue
        m=re.match(r'\[(\S+ \S+)\] \[t=([\d.]+)\] (.*)',line.strip())
        if m: ev.append((os.path.basename(f),m.group(1),float(m.group(2)),m.group(3)))
num=lambda s,pat: float(re.search(pat,s).group(1).rstrip('.'))
out={}
pin=[e for e in ev if 'PIN check' in e[3]]
out['pin_checks']=len(pin); out['pin_accepted']=sum('accepted' in e[3] for e in pin)
gp=[num(e[3],r'score=([\d.]+)') for e in ev if 'Factor 2 (Gesture) passed' in e[3]]
gf=[num(e[3],r'score=([\d.]+)') for e in ev if 'Gesture) failed locally' in e[3]]
out['gesture_pass']=gp; out['gesture_fail']=gf
mp=[num(e[3],r'in ([\d.]+)s') for e in ev if 'MFA PASSED' in e[3]]
out['mfa_pass_times']=mp
out['revokes']=[(e[0],e[2],e[3]) for e in ev if e[3].startswith('REVOKED')]
out['discarded']=sum('discarded' in e[3] for e in ev)
out['gesture_enrol']=sum(('Gesture ENROLLED' in e[3]) for e in ev)
out['sessions']=len(L)
out['anomaly']=[(e[0],e[2],num(e[3],r'speed=([\d.]+)'),num(e[3],r'z=([\d.]+)')) for e in ev if e[3].startswith('ANOMALY')]
json.dump(out,open('data/real_summary.json','w'),indent=1)
print('sessions',len(L),'PIN',out['pin_checks'],out['pin_accepted'])
print('gesture pass n',len(gp),'mean',round(st.mean(gp),3),'min',min(gp),'max',max(gp))
print('gesture fail n',len(gf),'mean',round(st.mean(gf),3),'range',min(gf),max(gf))
print('MFA pass n',len(mp),'median',st.median(mp),'range',min(mp),max(mp))
print('discarded',out['discarded'],'gesture enrol',out['gesture_enrol'])
from collections import Counter
print(Counter('biometric' if 'continuous biometric' in r[2] else 'spoof' for r in out['revokes']))
sp=[a[2] for a in out['anomaly']]; print('anomaly n',len(sp),'speed median',st.median(sp),'min',min(sp))
