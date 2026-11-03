"""Regenerates the Section 4 numbers and plots from the real session CSVs in this folder.
Data: 4 team members (P01-P04), 11 sessions (S01-S11). In each session the member deliberately
behaved differently to stand in for a different user, then at the end deliberately changed their
movement to test the lockout. Run: python make_section4_plots.py  (numpy, matplotlib)
Optional: sus_tlx_responses.csv (participant,SUS1..SUS10,TLX_mental..TLX_frustration)."""
import csv, os, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
SUM = list(csv.DictReader(open(os.path.join(HERE, 'sessions_summary.csv'))))
FEAT = None
def load(s):
    global FEAT
    rows = list(csv.DictReader(open(os.path.join(HERE, s + '_window_scores.csv'), encoding='utf-8-sig')))
    FEAT = list(rows[0].keys())[5:]
    E = np.array([[float(r[k]) for k in FEAT] for r in rows if r['state'] == 'Enrolling'])
    return rows, E
FLOOR = np.array([0.02, 0.02, 2, 2, 0.1, 1, 0.03, 0.03, 0.03, 0.03, 0.01, 0.005, 0.01, 0.015, 1.5, 0.02])
def template(W):
    mu = W.mean(0); sd = np.maximum(W.std(0, ddof=1), np.maximum(FLOOR, 0.02 * np.abs(mu))); return mu, sd
def score(t, X):
    z = np.clip((X - t[0]) / t[1], -6, 6); return np.exp(-0.5 * (z ** 2).mean(1))
def eer(g, im):
    th = np.linspace(0, 1, 2001); far = np.array([(im >= x).mean() for x in th]); frr = np.array([(g < x).mean() for x in th])
    k = np.argmin(abs(far - frr)); return (far[k] + frr[k]) / 2
def stats(name, v):
    v = np.array(v, float); print(f'{name}: N={len(v)} mean={v.mean():.3f} SD={v.std(ddof=1):.3f} median={np.median(v):.3f} min={v.min():.3f} max={v.max():.3f}')
S = [s['session'] for s in SUM]; P = [s['participant'] for s in SUM]; n = len(S)
data = [load(s) for s in S]
T = [template(E[:68]) for _, E in data]; H = [E[74:] for _, E in data]
gen, same, diff = [], [], []
per_session_eer = []
for i in range(n):
    gi = score(T[i], H[i]); gen.append(gi)
    imp_i = np.concatenate([score(T[i], H[j]) for j in range(n) if P[j] != P[i]]); diff.append(imp_i)
    sp = [score(T[i], H[j]) for j in range(n) if j != i and P[j] == P[i]]
    if sp: same.append(np.concatenate(sp))
    per_session_eer.append(eer(gi, imp_i))
g = np.concatenate(gen); d = np.concatenate(diff); sm = np.concatenate(same)
print(f'Pooled EER (own session vs other people): {eer(g, d)*100:.1f} %  | windows: {len(g)} genuine, {len(d)} impostor')
stats('Per-session EER', per_session_eer)
print(f'Mean score: own session {g.mean():.3f} | same person, other (deliberately different) session {sm.mean():.3f} | other people {d.mean():.3f}')
stats('MFA login time s', [s['mfa_login_s'] for s in SUM])
stats('Gesture verification score', [s['gesture_verify_score'] for s in SUM])
stats('First warning to lockout s', [s['first_warning_to_lockout_s'] for s in SUM if s['first_warning_to_lockout_s']])
no = [float(r['score']) for r in csv.DictReader(open(os.path.join(HERE, 'gesture_non_owner_attempts.csv')))]
stats('Non-owner gesture score', no)
plt.rcParams.update({'font.size': 7, 'font.family': 'serif'})
fig, ax = plt.subplots(figsize=(3.4, 1.85))
ax.boxplot([g, sm, d], showfliers=False); ax.set_xticks([1, 2, 3])
ax.set_xticklabels(['own session\n(genuine)', 'same person,\nother session', 'different\nperson'], fontsize=5.8)
ax.axhline(0.15, ls=':', color='grey'); ax.text(3.45, 0.17, 'lockout threshold', fontsize=5, ha='right', color='grey')
ax.set_ylabel('match score', fontsize=6.5); ax.set_title('Window scores: 4 members, 11 sessions', fontsize=6.5)
fig.tight_layout(pad=0.3); fig.savefig(os.path.join(HERE, 's4_left_scores.png'), dpi=250)
fig, ax = plt.subplots(figsize=(3.4, 1.85))
ax.boxplot([np.array(per_session_eer) * 100, np.array([float(s['gesture_verify_score']) for s in SUM]) * 100, np.array(no) * 100])
ax.set_xticks([1, 2, 3]); ax.set_xticklabels(['EER %\n(per session)', 'gesture score\nowner', 'gesture score\nnon-owner'], fontsize=5.8)
ax.axhline(65, ls=':', color='grey'); ax.text(3.45, 67, 'gesture threshold 65', fontsize=5, ha='right', color='grey')
ax.set_ylim(0, 100); ax.set_title('Primary metric (EER) and gesture factor', fontsize=6.5)
fig.tight_layout(pad=0.3); fig.savefig(os.path.join(HERE, 's4_right_metric.png'), dpi=250)
Sv = os.path.join(HERE, 'sus_tlx_responses.csv')
if os.path.exists(Sv):
    R = list(csv.DictReader(open(Sv)))
    sus = [2.5 * (sum(int(r[f'SUS{i}']) - 1 for i in (1, 3, 5, 7, 9)) + sum(5 - int(r[f'SUS{i}']) for i in (2, 4, 6, 8, 10))) for r in R]
    stats('SUS', sus)
    if all(r.get('TLX_mental') for r in R):
        stats('NASA-TLX raw', [np.mean([float(r[k]) for k in ('TLX_mental', 'TLX_physical', 'TLX_temporal', 'TLX_performance', 'TLX_effort', 'TLX_frustration')]) for r in R])
