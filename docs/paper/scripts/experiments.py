import numpy as np, json, time
from sim import run, eer, operational, legacy_spoof, motion, session_of, windows, HZ, SEED
from engine import Template

t0 = time.time()
R = {}
N = 40

def boot_eer(res, B=300, seed=7):
    rng = np.random.default_rng(seed)
    T, n = res['T'], res['N']
    # per-user genuine and impostor score lists for user-level bootstrap
    genB = [None] * n
    vals = []
    gB_u = np.split(res['gB'], np.cumsum([0]))  # placeholder (not used)
    return None

# ---------- E1: main condition ----------
main = run(N=N, win=3.0)
e_same = eer(main['gA'], main['imp']); e_cross = eer(main['gB'], main['imp'])
e_nn = eer(main['gB'], main['imp_nn'])
auc = float((main['gB'][:, None] > main['imp'][None, ::7]).mean())
R['E1'] = dict(N=N, n_gen_same=int(len(main['gA'])), n_gen_cross=int(len(main['gB'])), n_imp=int(len(main['imp'])),
               eer_same=float(e_same[0]), eer_cross=float(e_cross[0]), eer_thr_cross=float(e_cross[1]),
               eer_samebuild=float(e_nn[0]), auc_cross=auc,
               far_025=float((main['imp'] >= 0.25).mean()), frr_025_same=float((main['gA'] < 0.25).mean()),
               frr_025_cross=float((main['gB'] < 0.25).mean()),
               far_025_samebuild=float((main['imp_nn'] >= 0.25).mean()),
               gen_mean=float(main['gB'].mean()), imp_mean=float(main['imp'].mean()))
np.savez('../data/sim_main_scores.npz', gA=main['gA'], gB=main['gB'], imp=main['imp'], imp_nn=main['imp_nn'])
det = {}
for name, g, im in [('same', main['gA'], main['imp']), ('cross', main['gB'], main['imp']), ('samebuild', main['gB'], main['imp_nn'])]:
    _, _, ths, far, frr = eer(g, im); det[name] = dict(far=far.tolist(), frr=frr.tolist())

# bootstrap CI of cross-session EER, resampling users
rng = np.random.default_rng(11)
Wb = []
seg = np.cumsum([0] + [len(x) for x in [None]] ) if False else None
# rebuild per-user genuine / impostor score blocks
T, S = main['T'], main['streamB']
GB = [T[i].score(windows(S[i])[0]) for i in range(N)]
WB = [windows(S[j])[0] for j in range(N)]
IMP = [[T[i].score(WB[j]) for j in range(N) if j != i] for i in range(N)]
boots = []
for b in range(200):
    idx = rng.integers(0, N, N)
    g = np.concatenate([GB[i] for i in idx]); im = np.concatenate([np.concatenate(IMP[i]) for i in idx])
    boots.append(eer(g, im)[0])
R['E1']['eer_cross_ci'] = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
per_user_eer = [eer(GB[i], np.concatenate(IMP[i]))[0] for i in range(N)]
R['E1']['per_user_eer_median'] = float(np.median(per_user_eer))
R['E1']['per_user_eer_p90'] = float(np.percentile(per_user_eer, 90))
R['E1']['users_eer_le5'] = int(sum(e <= 0.05 for e in per_user_eer))
print('E1', time.time() - t0, R['E1'])

# ---------- E2: window length ----------
R['E2'] = {}
for w in [1.0, 2.0, 3.0, 4.0, 5.0]:
    r = main if w == 3.0 else run(N=N, win=w)
    R['E2'][str(w)] = dict(eer_same=float(eer(r['gA'], r['imp'])[0]), eer_cross=float(eer(r['gB'], r['imp'])[0]))
    print('E2', w, R['E2'][str(w)], time.time() - t0)

# ---------- E3: operational decision rule ----------
R['E3'] = {}
for k in [2, 3, 4, 5, 6]:
    o = operational(main, k=k, thr=0.25)
    L = o['latency']
    R['E3'][f'k{k}_t0.25'] = dict(false_lockouts=o['false_lockouts'], sessions=o['genuine_sessions'], minutes=o['genuine_minutes'],
                                  detected=o['detected'], trials=o['trials'], lat_mean=float(L.mean()) if len(L) else None,
                                  lat_sd=float(L.std()) if len(L) else None, lat_p95=float(np.percentile(L, 95)) if len(L) else None,
                                  lat_max=float(L.max()) if len(L) else None)
    if k == 4:
        np.save('../data/sim_latency_k4.npy', L)
    print('E3', k, R['E3'][f'k{k}_t0.25'], time.time() - t0)
for thr in [0.15, 0.35, 0.45]:
    o = operational(main, k=4, thr=thr); L = o['latency']
    R['E3'][f'k4_t{thr}'] = dict(false_lockouts=o['false_lockouts'], sessions=o['genuine_sessions'], detected=o['detected'],
                                 trials=o['trials'], lat_mean=float(L.mean()) if len(L) else None)
    print('E3 thr', thr, R['E3'][f'k4_t{thr}'])

# ---------- E4: feature ablation ----------
dyn = np.arange(0, 10); geo = np.arange(10, 16)
R['E4'] = {}
for name, m in [('dynamics', dyn), ('geometry', geo), ('all', None)]:
    g = np.concatenate([T[i].score(windows(S[i])[0], mask=m) for i in range(N)])
    im = np.concatenate([T[i].score(WB[j], mask=m) for i in range(N) for j in range(N) if j != i])
    R['E4'][name] = float(eer(g, im)[0])
print('E4', R['E4'])

# ---------- E5: posture change (sit <-> stand) ----------
post = run(N=N, win=3.0, posture=-0.30)
R['E5'] = dict(eer_cross=float(eer(post['gB'], post['imp'])[0]), frr_025=float((post['gB'] < 0.25).mean()))
o = operational(post, k=4, thr=0.25)
R['E5'].update(false_lockouts=o['false_lockouts'], sessions=o['genuine_sessions'])
print('E5', R['E5'])

# ---------- E6: legacy speed-threshold detector on genuine enrolment minutes ----------
rng = np.random.default_rng(SEED + 5)
rev, times = 0, []
for p in main['P']:
    st = motion(session_of(p, rng, day_shift=False), 60, rng)
    tt = legacy_spoof(st[1])
    if tt is not None:
        rev += 1; times.append(tt)
R['E6'] = dict(genuine_sessions=len(main['P']), revoked=rev, median_time=float(np.median(times)) if times else None)
print('E6', R['E6'])

# ---------- E7: enrolment duration ----------
R['E7'] = {}
rng = np.random.default_rng(SEED + 9)
for dur in [10, 20, 30, 60]:
    m = int((dur - 3) / 0.5) + 1
    Td = [Template(windows(motion(session_of(p, rng, day_shift=False), 60, rng))[0][:m]) for p in main['P']]
    g = np.concatenate([Td[i].score(windows(S[i])[0]) for i in range(N)])
    im = np.concatenate([Td[i].score(WB[j]) for i in range(N) for j in range(N) if j != i])
    R['E7'][str(dur)] = float(eer(g, im)[0])
print('E7', R['E7'])

json.dump(R, open('../data/sim_results.json', 'w'), indent=1)
json.dump(det, open('../data/sim_det.json', 'w'))
print('done', time.time() - t0)
