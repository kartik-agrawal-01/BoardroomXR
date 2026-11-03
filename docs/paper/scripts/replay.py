import numpy as np, json, pickle
from engine import Template, decide
PRE = {'Strict': (0.25, 4), 'Balanced': (0.15, 6), 'Relaxed': (0.10, 8)}
def replay(TT, H, mask=None):
    N = len(TT); out = {}
    for name, (th, k) in PRE.items():
        fl = 0; elig = 0; det = 0; lat = []
        for i in range(N):
            gi = TT[i].score(H[i], mask=mask)
            fl += decide(gi, threshold=th, k=k)[0] is not None
            for j in range(N):
                if j == i: continue
                idx, _ = decide(np.r_[gi, TT[i].score(H[j], mask=mask)], threshold=th, k=k)
                if idx is not None and idx < len(gi): continue
                elig += 1
                if idx is not None: det += 1; lat.append((idx - len(gi) + 1) * 0.5)
        out[name] = dict(threshold=th, k=k, genuine_streams=N, false_lock=fl, eligible=elig, detected=det,
                         det_rate=det / max(1, elig), lat_mean=float(np.mean(lat)) if lat else None,
                         lat_median=float(np.median(lat)) if lat else None, lat_p95=float(np.percentile(lat, 95)) if lat else None)
    return out
if __name__ == '__main__':
    S = pickle.load(open('../data/day2_S.pkl', 'rb'))
    TT = [Template(s['E'][:68]) for s in S]; H = [s['E'][74:] for s in S]
    r = replay(TT, H); print(json.dumps(r, indent=1))
    rg = replay(TT, H, mask=np.arange(10, 16)); print('geo', json.dumps({k: (v['false_lock'], v['detected'], v['eligible'], v['lat_mean']) for k, v in rg.items()}))
    json.dump(dict(all=r, geo=rg), open('../data/day2_replay.json', 'w'), indent=1)
