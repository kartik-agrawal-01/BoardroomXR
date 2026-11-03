import numpy as np, json, time
from sim_field import population2, protocol_eers
REAL = dict(A_all=0.309, C_all=0.167, A_geo=0.200, A_dyn=0.480)
rng = np.random.default_rng(5); res = []; t0 = time.time()
for it in range(160):
    prm = dict(c=rng.uniform(0.05, 1.0), sa=rng.uniform(0, 1.0), sh=rng.uniform(0, 0.06), st=rng.uniform(0, 1.2), sth=rng.uniform(0, 0.08))
    _, E, _ = population2(20, 77, **prm)
    e = protocol_eers(E)
    loss = sum((e[k] - REAL[k]) ** 2 for k in REAL)
    res.append(dict(**prm, loss=loss, **e))
    if it % 20 == 0: print(it, round(time.time() - t0))
res.sort(key=lambda r: r['loss'])
for r in res[:6]: print({k: round(v, 3) for k, v in r.items()})
json.dump(res, open('../data/field_calibration_search.json', 'w'), indent=1)
