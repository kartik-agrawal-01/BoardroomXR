import numpy as np, json, pickle, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import norm
from engine import Template
from sim import eer
exec(open('figs.py').read().split('# ---- Fig: real on-device score trace')[0])   # shared style
D = '../data/'; O = '../figs/'
S = pickle.load(open(D + 'day2_S.pkl', 'rb')); n = len(S)

# ---- F2: field trace (session S10 = index 9)
s = S[9]; t = s['t']; st = s['st']; ver = np.where(st != 'Enrolling')[0]; t0 = t[ver[0]]
fig, ax = plt.subplots(figsize=(W1, 1.75))
ax.axvspan(-62, 0, color='#eeede8', lw=0); ax.text(-31, 0.93, 'enrolment (60 s, 114 windows)', ha='center', fontsize=6.5, color=INK2)
tv = t[ver] - t0
ax.plot(tv, s['raw'][ver], color=C[0], marker='o', ms=2.2, lw=0.8, label='raw window score $S$')
ax.plot(tv, s['sm'][ver], color=C[1], ls='--', lw=1.3, label='smoothed score')
ax.axhline(0.15, color=INK2, lw=0.8, ls=':'); ax.text(-60, 0.17, r'Balanced $\theta=0.15$', fontsize=6.5, color=INK2)
w = np.where(st == 'Warning')[0]; lk = np.where(st == 'LockedOut')[0][0]
ax.axvspan(t[w[0]] - t0, t[lk] - t0, color='#f6d9c9', lw=0)
ax.annotate('induced behaviour change\n(first warning)', xy=(t[w[0]] - t0, s['sm'][w[0]]), xytext=(-36, 0.50), fontsize=6.5, arrowprops=dict(arrowstyle='->', color=INK2, lw=0.6))
ax.annotate('lockout (6th violation)', xy=(t[lk] - t0, s['sm'][lk]), xytext=(-36, 0.30), fontsize=6.5, arrowprops=dict(arrowstyle='->', color=INK2, lw=0.6))
ax.set_xlim(-62, t[lk] - t0 + 2); ax.set_ylim(0, 1); ax.set_xlabel('time relative to end of enrolment (s)'); ax.set_ylabel('match score')
grid(ax); ax.legend(loc='upper left', bbox_to_anchor=(0.0, 0.88), handlelength=1.6)
fig.savefig(O + 'field_trace.pdf'); fig.savefig(O + 'field_trace.png', dpi=200); plt.close(fig)

# ---- F3: cross-score matrix
M = np.load(D + 'day2_crossmatrix.npy')
order = np.argsort([s['f'].split('_')[-1] for s in S])   # chronological session order
M = M[np.ix_(order, order)]
fig, ax = plt.subplots(figsize=(W1, 2.55))
im = ax.imshow(M, cmap='Blues', vmin=0, vmax=0.85)
for i in range(n):
    for j in range(n):
        ax.text(j, i, f'{M[i, j]:.2f}'.lstrip('0') if M[i, j] < 1 else '1', ha='center', va='center', fontsize=4.6,
                color='white' if M[i, j] > 0.5 else INK, fontweight='bold' if i == j else 'normal')
PER = json.load(open(D + 'day2_people.json'))['person']
lab = [f'S{k+1:02d} ({PER[k]})' for k in range(n)]
ax.set_xticks(range(n)); ax.set_xticklabels(lab, rotation=90, fontsize=5.0); ax.set_yticks(range(n)); ax.set_yticklabels(lab, fontsize=5.0)
ax.set_xlabel('session whose windows are scored'); ax.set_ylabel('template (enrolled session)')
for sp in ax.spines.values(): sp.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.ax.tick_params(labelsize=6); cb.set_label('mean match score', fontsize=7)
fig.savefig(O + 'field_matrix.pdf'); fig.savefig(O + 'field_matrix.png', dpi=200); plt.close(fig)
json.dump({'order': [S[k]['f'] for k in order]}, open(D + 'day2_session_order.json', 'w'), indent=1)

# ---- F4: DET
sc = np.load(D + 'day2_scores.npz'); ss = np.load(D + 'sim_main_scores.npz')
from sim_field import A_tr, A_te, C_tr, C_te
order_ = json.load(open(D + 'day2_session_order.json'))['order']; byf_ = {s['f']: s for s in S}; SC = [byf_[f] for f in order_]
PER = json.load(open(D + 'day2_people.json'))['person']; dp = lambda i, j: PER[i] != PER[j]
TT = [Template(s['E'][C_tr]) for s in SC]
gC = np.concatenate([TT[i].score(SC[i]['E'][C_te]) for i in range(n)]); iC = np.concatenate([TT[i].score(SC[j]['E'][C_te]) for i in range(n) for j in range(n) if dp(i, j)])
TA_ = [Template(s['E'][A_tr]) for s in SC]
gA_ = np.concatenate([TA_[i].score(SC[i]['E'][A_te]) for i in range(n)]); iA_ = np.concatenate([TA_[i].score(SC[j]['E'][A_te]) for i in range(n) for j in range(n) if dp(i, j)])
from field_experiments import gen, SETS
E = gen(40, 1301, SETS[1], 60); TF = [Template(e[:68]) for e in E]
gF = np.concatenate([TF[i].score(E[i][74:114]) for i in range(40)]); iF = np.concatenate([TF[i].score(E[j][74:114]) for i in range(40) for j in range(40) if i != j])
series = [('idealised sim., cross-session', ss['gB'], ss['imp'], C[0], '-'), ('team study, interleaved', gC, iC, C[2], '-.'),
          ('team study, held-out end', gA_, iA_, C[1], '--'), ('re-calibrated sim.', gF, iF, C[3], ':')]
fig, ax = plt.subplots(figsize=(W1, 2.6)); pt = lambda p: norm.ppf(np.clip(p, 1e-4, 1 - 1e-4))
eers = {}
for lab_, g, im_, c, ls in series:
    e, _, _, far, frr = eer(g, im_); eers[lab_] = float(e)
    ax.plot(pt(far), pt(frr), color=c, ls=ls, label=f'{lab_} ({e*100:.1f}%)')
ax.plot(pt(np.array([1e-3, 0.7])), pt(np.array([1e-3, 0.7])), color=GRID, lw=0.8)
ticks = np.array([0.001, 0.01, 0.05, 0.2, 0.5])
ax.set_xticks(pt(ticks)); ax.set_xticklabels([f'{x*100:g}' for x in ticks]); ax.set_yticks(pt(ticks)); ax.set_yticklabels([f'{x*100:g}' for x in ticks])
ax.set_xlim(pt(0.0008), pt(0.8)); ax.set_ylim(pt(0.0008), pt(0.8))
ax.set_xlabel('false acceptance rate (%)'); ax.set_ylabel('false rejection rate (%)'); grid(ax); ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=5.8, columnspacing=0.8, handlelength=1.8)
fig.savefig(O + 'det2.pdf'); fig.savefig(O + 'det2.png', dpi=200); plt.close(fig)
json.dump(eers, open(D + 'det2_eers.json', 'w'), indent=1)

# ---- F5: feature groups
rp = json.load(open(D + 'day2_people.json'))['R']; real = {'eer_dynamics': rp['A_people_dyn'], 'eer_geometry': rp['A_people_geo'], 'eer': rp['A_people']['eer']}; ide = json.load(open(D + 'sim_results.json'))['E4']
fs = json.load(open(D + 'field_calibration_search.json'))[:3]
groups = ['dynamics', 'geometry', 'all 16']
vals = {'idealised sim.': [ide['dynamics'], ide['geometry'], ide['all']],
        'team study (4 people)': [real['eer_dynamics'], real['eer_geometry'], real['eer']],
        're-calibrated sim.': [np.mean([f['A_dyn'] for f in fs]), np.mean([f['A_geo'] for f in fs]), np.mean([f['A_all'] for f in fs])]}
fig, ax = plt.subplots(figsize=(W1, 1.65)); x = np.arange(3); wdt = 0.26
for k, (lab_, v) in enumerate(vals.items()):
    b = ax.bar(x + (k - 1) * wdt, np.array(v) * 100, wdt, color=[C[0], C[1], C[3]][k], label=lab_)
    for xx, vv in zip(x + (k - 1) * wdt, v): ax.text(xx, vv * 100 + 1, f'{vv*100:.0f}', ha='center', fontsize=5.6, color=INK2)
ax.axhline(5, color=INK2, lw=0.7, ls=':'); ax.text(0.5, 6.2, '5% target', fontsize=5.4, color=INK2, ha='center')
ax.set_xticks(x); ax.set_xticklabels(groups); ax.set_ylabel('EER (%)'); ax.set_ylim(0, 58); grid(ax); ax.legend(fontsize=6, loc='upper right')
fig.savefig(O + 'groups.pdf'); fig.savefig(O + 'groups.png', dpi=200); plt.close(fig)
json.dump(vals, open(D + 'groups_vals.json', 'w'), indent=1)

# ---- F6: remedies (field-calibrated sim)
FE = json.load(open(D + 'field_experiments.json'))
Ds = [36, 60, 120, 180]
fig, ax = plt.subplots(figsize=(W1, 1.7))
for k, (key, lab_, mk) in enumerate([('all', 'all features', 'o'), ('geo', 'geometry only', 's'), ('geo_agg', 'geometry + 5 s averaging', '^')]):
    arr = np.array([[FE[str(si)][f'D{d}_{key}']['eer'] for d in Ds] for si in range(3)]) * 100
    ax.fill_between(Ds, arr.min(0), arr.max(0), color=C[k], alpha=0.15, lw=0)
    ax.plot(Ds, arr.mean(0), color=C[k], marker=mk, ms=3.5, label=lab_)
ax.axhline(5, color=INK2, lw=0.7, ls=':'); ax.text(178, 6.2, '5% target', fontsize=5.8, color=INK2, ha='right')
ax.set_xlabel('enrolment duration (s)'); ax.set_ylabel('EER (%)'); ax.set_ylim(0, 34); ax.set_xticks(Ds); grid(ax); ax.legend(fontsize=6, loc='lower left', ncol=1)
fig.savefig(O + 'remedies.pdf'); fig.savefig(O + 'remedies.png', dpi=200); plt.close(fig)
print('ok', eers)
