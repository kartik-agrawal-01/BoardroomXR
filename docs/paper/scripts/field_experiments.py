import numpy as np, json, time
from sim_field import person_field, motion_field2, A_tr, A_te, C_tr, C_te, geo
from sim import windows, session_of, eer, HZ
from engine import Template, decide
search = json.load(open('../data/field_calibration_search.json'))
SETS = [{k: search[i][k] for k in ('c', 'sa', 'sh', 'st', 'sth')} for i in range(3)]
PRE = {'Strict': (0.25, 4), 'Balanced': (0.15, 6), 'Relaxed': (0.10, 8)}
def agg(s, w): return np.convolve(s, np.ones(w) / w, 'valid') if w > 1 else s
def gen(N, seed, prm, dur):
    rng = np.random.default_rng(seed)
    P = [person_field(rng, prm['c']) for _ in range(N)]
    return [windows(motion_field2(session_of(p, rng, day_shift=False), dur, rng, prm['sa'], prm['sh'], prm['st'], prm['sth']))[0] for p in P]
def evaluate(E, n_tr, mask=None, w=1):
    N = len(E); TT = [Template(e[:n_tr]) for e in E]; H = [e[n_tr + 6:n_tr + 46] for e in E]
    g = np.concatenate([agg(TT[i].score(H[i], mask=mask), w) for i in range(N)])
    im = np.concatenate([agg(TT[i].score(H[j], mask=mask), w) for i in range(N) for j in range(N) if i != j])
    out = dict(eer=float(eer(g, im)[0]))
    for name, (th, k) in PRE.items():
        fl = 0; det = 0; lat = []; tr = 0
        for i in range(N):
            gi = TT[i].score(H[i], mask=mask)
            fl += decide(gi, threshold=th, k=k)[0] is not None
            for j in range(N):
                if j == i: continue
                idx, _ = decide(np.r_[gi, TT[i].score(H[j], mask=mask)], threshold=th, k=k); tr += 1
                if idx is not None and idx >= len(gi): det += 1; lat.append((idx - len(gi) + 1) * 0.5)
        out[name] = dict(false_lock=fl / N, det=det / tr, lat=float(np.mean(lat)) if lat else None)
    return out
if __name__ == "__main__":
    R = {}; t0 = time.time()
    for si, prm in enumerate(SETS):
        R[si] = dict(params=prm)
        for D in [36, 60, 120, 180]:
            n_tr = int((D - 3) / 0.5) + 1
            E = gen(40, 900 + si, prm, D + 23.5)
            R[si][f'D{D}_all'] = evaluate(E, n_tr)
            R[si][f'D{D}_geo'] = evaluate(E, n_tr, mask=geo)
            R[si][f'D{D}_geo_agg'] = evaluate(E, n_tr, mask=geo, w=10)
            print(si, D, {k: round(v['eer'], 3) for k, v in R[si].items() if k.startswith(f'D{D}_')}, round(time.time() - t0))
    json.dump(R, open('../data/field_experiments.json', 'w'), indent=1)
