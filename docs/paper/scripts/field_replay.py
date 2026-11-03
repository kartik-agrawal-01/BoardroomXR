import numpy as np, json
from field_experiments import gen, SETS
from replay import replay
from engine import Template
from sim import eer
out = {}
for si, prm in enumerate(SETS):
    E = gen(40, 1300 + si, prm, 60)
    TT = [Template(e[:68]) for e in E]; H = [e[74:114] for e in E]
    g = np.concatenate([TT[i].score(H[i]) for i in range(40)]); im = np.concatenate([TT[i].score(H[j]) for i in range(40) for j in range(40) if i != j])
    out[si] = dict(eer=float(eer(g, im)[0]), all=replay(TT, H), geo=replay(TT, H, mask=np.arange(10, 16)))
    for m in ('all', 'geo'):
        print(si, m, round(out[si]['eer'], 3), {k: (round(v['false_lock'] / 40, 2), round(v['det_rate'], 2), round(v['lat_mean'] or 0, 1)) for k, v in out[si][m].items()})
json.dump(out, open('../data/field_replay.json', 'w'), indent=1)
