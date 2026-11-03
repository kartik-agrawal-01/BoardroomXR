import numpy as np, json, csv, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import norm

C = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4']
INK, INK2, GRID = '#1f1f1e', '#5c5b55', '#d9d8d2'
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['STIXGeneral'], 'mathtext.fontset': 'stix',
                     'font.size': 8, 'axes.labelsize': 8, 'axes.titlesize': 8, 'legend.fontsize': 7,
                     'xtick.labelsize': 7, 'ytick.labelsize': 7, 'axes.edgecolor': INK2, 'axes.linewidth': 0.6,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.labelcolor': INK, 'text.color': INK,
                     'axes.spines.top': False, 'axes.spines.right': False, 'lines.linewidth': 1.4,
                     'legend.frameon': False, 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.02})
W1 = 3.45
D = '/home/claude/paper/data/'
O = '/home/claude/paper/figs/'

def grid(ax):
    ax.grid(True, color=GRID, lw=0.5); ax.set_axisbelow(True)

# ---- Fig: real on-device score trace (V2 session) ----
rows = list(csv.DictReader(open(D + 'headset_logs/BiometricLogs/scores_EMP-2e373121_enrol_20261026_061344.csv', encoding='utf-8-sig')))
t = np.array([float(r['t']) for r in rows]); st = [r['state'] for r in rows]
raw = np.array([float(r['raw_score']) for r in rows]); sm = np.array([float(r['smoothed_score']) for r in rows])
ver = [i for i, s in enumerate(st) if s != 'Enrolling']
fig, ax = plt.subplots(figsize=(W1, 1.75))
t0 = t[ver[0]]
ax.axvspan(t[0] - t0, 0, color='#eeede8', lw=0)
ax.text(-15, 0.93, 'enrolment (60 s, 114 windows)', ha='center', va='center', fontsize=6.5, color=INK2)
tv = t[ver] - t0
ax.plot(tv, raw[ver], color=C[0], marker='o', ms=3, lw=1.0, label='raw window score $S$')
ax.plot(tv, sm[ver], color=C[1], ls='--', lw=1.4, label='smoothed score')
ax.axhline(0.25, color=INK2, lw=0.8, ls=':'); ax.text(-29, 0.27, r'threshold $\theta=0.25$', fontsize=6.5, color=INK2)
lk = [i for i, s in enumerate(st) if s == 'LockedOut'][0]
ax.annotate('lockout,\naccess revoked', xy=(t[lk] - t0, sm[lk]), xytext=(8.2, 0.33), fontsize=6.5,
            arrowprops=dict(arrowstyle='->', color=INK2, lw=0.6), color=INK)
ax.annotate('headset\nhanded over', xy=(1.9, 0.66), xytext=(6.0, 0.80), fontsize=6.5,
            arrowprops=dict(arrowstyle='->', color=INK2, lw=0.6), color=INK)
ax.set_xlim(-30, 15); ax.set_ylim(0, 1.0); ax.set_xlabel('time relative to end of enrolment (s)'); ax.set_ylabel('match score')
grid(ax); ax.legend(loc='upper left', bbox_to_anchor=(0.0, 0.84), handlelength=1.6)
fig.savefig(O + 'real_trace.pdf'); plt.close(fig)

# ---- Fig: real body geometry of volunteers ----
R = np.load(D + 'real_windows.npz'); keys = sorted(k for k in R.files if k.startswith('P_'))
mk = ['o', 's', '^', 'D', 'v']
fig, ax = plt.subplots(figsize=(W1, 1.9))
for i, k in enumerate(keys):
    F = R[k]
    ax.scatter(F[:, 10], F[:, 13], s=9, color=C[i], marker=mk[i], alpha=0.75, lw=0, label=f'V{i+1} ({len(F)} win.)')
ax.set_xlabel('mean head-to-right-controller distance (m)'); ax.set_ylabel('mean eye height (m)')
grid(ax); ax.legend(ncol=3, loc='upper center', bbox_to_anchor=(0.5, 1.22), columnspacing=0.8, handletextpad=0.2)
fig.savefig(O + 'real_geometry.pdf'); plt.close(fig)

# ---- Fig: score distributions (real pilot + simulation) ----
rs = np.load(D + 'real_scores.npz'); ss = np.load(D + 'sim_main_scores.npz')
fig, axs = plt.subplots(1, 2, figsize=(W1 * 2.05, 1.7))
bins = np.linspace(0, 1, 41)
for ax, g, im, ttl in [(axs[0], rs['gen'], rs['imp'], f'(a) On-device pilot: {len(rs["gen"])} genuine / {len(rs["imp"])} impostor windows'),
                       (axs[1], ss['gB'], ss['imp'], f'(b) Simulation, cross-session: {len(ss["gB"]):,} / {len(ss["imp"]):,} windows')]:
    ax.hist(im, bins=bins, density=True, color=C[1], alpha=0.85, label='impostor', edgecolor='white', lw=0.4)
    ax.hist(g, bins=bins, density=True, color=C[0], alpha=0.75, label='genuine', edgecolor='white', lw=0.4)
    ax.axvline(0.25, color=INK2, ls=':', lw=0.8)
    ax.set_yscale('log'); ax.set_xlabel('match score $S$'); ax.set_ylabel('density (log)'); ax.set_title(ttl, loc='left')
    grid(ax); ax.legend(loc='upper right')
fig.tight_layout(w_pad=1.5); fig.savefig(O + 'score_dist.pdf'); plt.close(fig)

# ---- Fig: DET curves ----
det = json.load(open(D + 'sim_det.json'))
def det_from(g, im):
    th = np.linspace(0, 1, 2001)
    return np.array([(im >= x).mean() for x in th]), np.array([(g < x).mean() for x in th])
fig, ax = plt.subplots(figsize=(W1, 2.3))
pt = lambda p: norm.ppf(np.clip(p, 1e-4, 1 - 1e-4))
series = [('sim. same-session', det['same'], C[0], '-'), ('sim. cross-session', det['cross'], C[1], '--'),
          ('sim. same-build impostors', det['samebuild'], C[2], '-.')]
far, frr = det_from(rs['gen'], rs['imp'])
series.append(('on-device pilot', dict(far=far, frr=frr), C[3], ':'))
res = json.load(open(D + 'sim_results.json')); rp = json.load(open(D + 'real_pilot_results.json'))
eers = [res['E1']['eer_same'], res['E1']['eer_cross'], res['E1']['eer_samebuild'], rp['eer']]
for (lab, d, c, ls), e in zip(series, eers):
    ax.plot(pt(np.array(d['far'])), pt(np.array(d['frr'])), color=c, ls=ls, label=f'{lab} (EER {e*100:.1f}%)')
ax.plot(pt(np.array([1e-3, 0.6])), pt(np.array([1e-3, 0.6])), color=GRID, lw=0.8)
ticks = np.array([0.001, 0.01, 0.05, 0.2, 0.5])
ax.set_xticks(pt(ticks)); ax.set_xticklabels([f'{x*100:g}' for x in ticks]); ax.set_yticks(pt(ticks)); ax.set_yticklabels([f'{x*100:g}' for x in ticks])
ax.set_xlim(pt(0.0008), pt(0.7)); ax.set_ylim(pt(0.0008), pt(0.7))
ax.set_xlabel('false acceptance rate (%)'); ax.set_ylabel('false rejection rate (%)'); grid(ax)
ax.legend(loc='upper right', fontsize=6.3)
fig.savefig(O + 'det.pdf'); plt.close(fig)

# ---- Fig: operating points ----
op = json.load(open(D + 'sim_opsweep.json'))
fig, ax = plt.subplots(figsize=(W1, 2.0))
for ki, (k, m) in enumerate([(4, 'o'), (6, 's'), (8, '^')]):
    pts = [v for v in op.values() if v['k'] == k and v['lat_mean'] is not None]
    x = [v['lat_mean'] for v in pts]; y = [100 * v['false_lockout_sessions'] / v['sessions'] for v in pts]
    ax.plot(x, y, color=C[ki], marker=m, ms=4.5, lw=1.0, label=f'$k={k}$ consecutive windows')
    for v, xx, yy in zip(pts, x, y):
        ax.annotate(f"{v['thr']:.2f}", (xx, yy), textcoords='offset points', xytext=(4, 2), fontsize=5.8, color=INK2)
ax.scatter([op['0.25_4']['lat_mean']], [100 * op['0.25_4']['false_lockout_sessions'] / 40], s=70, facecolor='none', edgecolor=INK, lw=0.9)
ax.annotate('deployed', (op['0.25_4']['lat_mean'], 100 * op['0.25_4']['false_lockout_sessions'] / 40), textcoords='offset points', xytext=(-4, -16), fontsize=6.5, fontweight='bold')
ax.scatter([op['0.1_8']['lat_mean']], [0], s=70, facecolor='none', edgecolor=INK, lw=0.9)
ax.annotate('recommended', (op['0.1_8']['lat_mean'], 0), textcoords='offset points', xytext=(-10, 14), fontsize=6.5, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=INK2, lw=0.6))
ax.set_xlabel('mean lockout latency after handover (s)'); ax.set_ylabel('genuine sessions with a\nfalse lockout (%)')
grid(ax); ax.legend(loc='upper right', fontsize=6.3); ax.set_xlim(2, 9)
fig.savefig(O + 'operating.pdf'); plt.close(fig)

# ---- Fig: window length + enrolment duration ----
fig, axs = plt.subplots(1, 2, figsize=(W1, 1.55), sharey=True)
w = sorted(res['E2'], key=float)
axs[0].plot([float(x) for x in w], [100 * res['E2'][x]['eer_same'] for x in w], color=C[0], marker='o', ms=3.5, label='same-session')
axs[0].plot([float(x) for x in w], [100 * res['E2'][x]['eer_cross'] for x in w], color=C[1], marker='s', ms=3.5, ls='--', label='cross-session')
axs[0].set_xlabel('window length $W$ (s)'); axs[0].set_ylabel('EER (%)'); axs[0].legend(fontsize=6); grid(axs[0])
e = sorted(res['E7'], key=float)
axs[1].plot([float(x) for x in e], [100 * res['E7'][x] for x in e], color=C[1], marker='s', ms=3.5, ls='--')
axs[1].set_xlabel('enrolment duration (s)'); grid(axs[1])
for a in axs: a.axhline(5, color=INK2, lw=0.7, ls=':')
axs[1].text(60, 5.3, '5% target', ha='right', fontsize=6, color=INK2)
fig.tight_layout(w_pad=0.6); fig.savefig(O + 'ablation.pdf'); plt.close(fig)
print('figures ok')
