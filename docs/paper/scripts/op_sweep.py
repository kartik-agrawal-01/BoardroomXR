import numpy as np, json
from sim import run, windows, concat, HZ, SEED
from engine import decide
main = run(N=40, win=3.0)
T, S, N = main['T'], main['streamB'], main['N']
rng = np.random.default_rng(SEED + 1)
pairs = [(i, j) for i in range(N) for j in rng.choice([x for x in range(N) if x != i], 5, replace=False)]
gen_scores = [T[i].score(windows(S[i])[0]) for i in range(N)]
ho = []
for i, j in pairs:
    st = concat(tuple(x[:30 * HZ] for x in S[i]), tuple(x[:30 * HZ] for x in S[j]))
    W, ends = windows(st); ho.append((T[i].score(W), ends))
out = {}
for thr in [0.05, 0.10, 0.15, 0.20, 0.25]:
    for k in [4, 6, 8]:
        fl = sum(decide(g, threshold=thr, k=k)[0] is not None for g in gen_scores)
        lat, eligible, det = [], 0, 0
        for sc, ends in ho:
            idx, _ = decide(sc, threshold=thr, k=k)
            if idx is not None and ends[idx] <= 30: continue   # false lockout before handover: not a detection trial
            eligible += 1
            if idx is not None: det += 1; lat.append(ends[idx] - 30)
        out[f'{thr}_{k}'] = dict(thr=thr, k=k, false_lockout_sessions=fl, sessions=N, eligible=eligible, detected=det,
                                 det_rate=det / max(1, eligible), lat_mean=float(np.mean(lat)) if lat else None,
                                 lat_p95=float(np.percentile(lat, 95)) if lat else None)
        print(thr, k, fl, f'{det}/{eligible}', round(np.mean(lat), 2) if lat else None, round(np.percentile(lat,95),2) if lat else None)
json.dump(out, open('../data/sim_opsweep.json', 'w'), indent=1)
