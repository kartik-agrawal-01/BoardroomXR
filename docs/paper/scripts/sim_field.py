"""Field-calibrated simulation: adds within-session activity regimes and posture drift
to the idealised motion model in sim.py. SIMULATED DATA."""
import numpy as np
from sim import ou, person, session_of, windows, HZ, _K
from engine import Template
from sim import eer

def piecewise(n, rng, sigma, seg=(4, 15), smooth=1.0, kind='log'):
    out = np.zeros(n); i = 0
    while i < n:
        L = int(rng.uniform(*seg) * HZ); v = rng.normal(0, sigma)
        out[i:i + L] = v; i += L
    k = np.exp(-0.5 * (np.arange(-3 * smooth * HZ, 3 * smooth * HZ + 1) / (smooth * HZ)) ** 2); k /= k.sum()
    out = np.convolve(np.r_[np.full(len(k)//2, out[0]), out, np.full(len(k)//2, out[-1])], k, 'valid')[:n]
    return np.exp(out) if kind == 'log' else out

def motion_field(q, dur, rng, sa=0.0, sh=0.0, sr=0.0):
    n = int(dur * HZ); t = np.arange(n) / HZ
    a = piecewise(n, rng, sa) if sa > 0 else np.ones(n)          # activity multiplier (head)
    ah = piecewise(n, rng, sa) if sa > 0 else np.ones(n)         # activity multiplier (hands)
    dh = piecewise(n, rng, sh, kind='lin') if sh > 0 else np.zeros(n)   # posture (eye height) drift, m
    rr = piecewise(n, rng, sr) if sr > 0 else np.ones(n)          # reach multiplier
    yaw = ou(n, q['yaw_tau'], q['yaw_sd'], rng) * a
    k = rng.poisson(q['turn_rate'] * dur * float(a.mean()))
    for _ in range(k):
        c = rng.uniform(0, dur); w = rng.uniform(0.3, 0.8); amp = q['turn_amp'] * rng.choice([-1, 1])
        yaw += amp * a[min(n - 1, int(c * HZ))] * np.exp(-0.5 * ((t - c) / (w / 2)) ** 2)
    pitch = q['p0'] + ou(n, 1.0, q['p_sd'], rng) - 40 * dh       # bending forward looks down
    body = ou(n, 4.0, 0.4 * q['yaw_sd'], rng)
    head = np.c_[ou(n, q['sway_tau'], q['sway'], rng) * a,
                 q['h'] + dh + ou(n, q['sway_tau'], 0.5 * q['sway'], rng) * a,
                 ou(n, q['sway_tau'], q['sway'], rng) * a] + rng.normal(0, q['trem'], (n, 3))
    y, x = np.radians(yaw) / 2, np.radians(pitch) / 2
    hrot = np.c_[np.cos(y) * np.sin(x), np.sin(y) * np.cos(x), -np.sin(y) * np.sin(x), np.cos(y) * np.cos(x)]
    by = np.radians(body)
    def hand(side, scale):
        off = np.c_[side * q['s'] + ou(n, q['hand_tau'], scale * q['hand_sd'], rng) * ah,
                    -q['d'] + ou(n, q['hand_tau'], 0.6 * scale * q['hand_sd'], rng) * ah,
                    q['r'] * rr * (1 if side > 0 else 0.92) + ou(n, q['hand_tau'], 0.5 * scale * q['hand_sd'], rng) * ah]
        rx = off[:, 0] * np.cos(by) + off[:, 2] * np.sin(by)
        rz = -off[:, 0] * np.sin(by) + off[:, 2] * np.cos(by)
        return head + np.c_[rx, off[:, 1], rz] + rng.normal(0, q['trem'], (n, 3))
    return t, head, hrot, hand(-1, 0.7), hand(1, 1.0)

A_tr = np.arange(68); A_te = np.arange(74, 114)
blocks = np.arange(114) // 20
C_tr = np.where(blocks % 2 == 0)[0]; C_te = np.array([i for i in range(114) if blocks[i] % 2 == 1 and i % 20 >= 6])
geo = np.arange(10, 16); dyn = np.arange(10)

def protocol_eers(E, masks=True):
    n = len(E); out = {}
    for name, tr, te in [('A', A_tr, A_te), ('C', C_tr, C_te)]:
        TT = [Template(e[tr]) for e in E]
        for mname, m in ([('all', None), ('geo', geo), ('dyn', dyn)] if masks and name == 'A' else [('all', None)]):
            g = np.concatenate([TT[i].score(E[i][te], mask=m) for i in range(n)])
            im = np.concatenate([TT[i].score(E[j][te], mask=m) for i in range(n) for j in range(n) if i != j])
            out[f'{name}_{mname}'] = float(eer(g, im)[0])
    return out

def population(N, seed, sa, sh, sr, dur=60):
    rng = np.random.default_rng(seed)
    P = [person(rng) for _ in range(N)]
    E = [windows(motion_field(session_of(p, rng, day_shift=False), dur, rng, sa, sh, sr))[0] for p in P]
    return P, E, rng

RANGES = dict(yaw_sd=(3, 40), yaw_tau=(1.0, 4.0), p_sd=(2, 7), turn_rate=(0.03, 0.25), turn_amp=(10, 60),
              sway=(0.04, 0.30), sway_tau=(0.8, 3), hand_sd=(0.08, 0.22), hand_tau=(0.2, 0.6), trem=(0.00004, 0.00016))

def person_field(rng, c=1.0):
    p = person(rng)
    for k, (lo, hi) in RANGES.items():
        m = 0.5 * (lo + hi); p[k] = m + c * (p[k] - m)
    return p

def trend(n, rng, st):
    if st <= 0: return np.ones(n)
    return np.exp(rng.normal(0, st) * np.linspace(-1, 1, n))

def motion_field2(q, dur, rng, sa, sh, st, sth):
    """sa: fast activity regimes; sh: fast posture drift (m); st: slow activity trend; sth: slow posture trend (m)."""
    tr = trend(int(dur * HZ), rng, st)
    th = rng.normal(0, sth) * np.linspace(-1, 1, int(dur * HZ)) if sth > 0 else 0
    q2 = dict(q)
    t, head, hrot, L, R = motion_field(q2, dur, rng, sa, sh, 0.0)
    # apply slow trend to motion amplitude around the session mean position, and slow posture trend
    for arr in (head, L, R):
        m = arr.mean(0)
        arr[:] = m + (arr - m) * tr[:, None]
        arr[:, 1] += th
    return t, head, hrot, L, R

def population2(N, seed, c, sa, sh, st, sth, dur=60):
    rng = np.random.default_rng(seed)
    P = [person_field(rng, c) for _ in range(N)]
    E = [windows(motion_field2(session_of(p, rng, day_shift=False), dur, rng, sa, sh, st, sth))[0] for p in P]
    return P, E, rng
