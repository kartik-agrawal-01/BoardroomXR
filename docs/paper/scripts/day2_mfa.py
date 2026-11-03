import re,glob,json,statistics as st
R=dict(sessions=0,pin_ok=0,pin_bad=0,g_enrol=0,g_enrol_match=[],g_pass=[],g_fail=[],g_disc=0,otp_ok=0,otp_bad=0,mfa_pass=[],timeouts=0,switch=0,switch_same=0,lockouts=0,enrol_done=0,spoof_would=0,stroke_dur=[])
for f in sorted(glob.glob('../data/day2/mfa/*.log')):
    R['sessions']+=1
    for l in open(f,encoding='utf-8-sig'):
        if 'PIN check' in l: R['pin_ok' if 'accepted' in l else 'pin_bad']+=1
        m=re.search(r'match to first stroke (\d+\.\d+)',l)
        if m: R['g_enrol_match'].append(float(m.group(1)))
        if 'gesture_enrol user' in l: R['g_enrol']+=1
        m=re.search(r'Gesture check for .*score=(\d+\.\d+).*-> (\w+)',l)
        if m: (R['g_pass'] if m.group(2)=='accepted' else R['g_fail']).append(float(m.group(1)))
        m=re.search(r'Factor 2 \(Gesture\) failed locally: score=(\d+\.\d+)',l)
        if m: R['g_fail'].append(float(m.group(1)))
        if 'stroke discarded' in l or 'Stroke discarded' in l: R['g_disc']+=1
        if 'OTP check' in l: R['otp_ok' if 'accepted' in l else 'otp_bad']+=1
        m=re.search(r'MFA PASSED in ([\d.]+)s',l)
        if m: R['mfa_pass'].append(float(m.group(1)))
        if 'TIMED OUT' in l: R['timeouts']+=1
        m=re.search(r'identity_switch user=(\S+) from=(\S+)',l)
        if m:
            R['switch']+=1; R['switch_same']+= m.group(1)==m.group(2)
        if 'lockout user' in l and 'BioEvt' in l: R['lockouts']+=1
        if 'enrol_done' in l: R['enrol_done']+=1
        if 'would revoke' in l: R['spoof_would']+=1
        m=re.search(r'submitted: (\d+) points over ([\d.]+)s',l)
        if m: R['stroke_dur'].append(float(m.group(2)))
for k,v in R.items():
    if isinstance(v,list) and v: print(k,len(v),'mean %.3f med %.3f min %.3f max %.3f'%(st.mean(v),st.median(v),min(v),max(v)))
    else: print(k,v)
json.dump(R,open('../data/day2_mfa.json','w'),indent=1)
