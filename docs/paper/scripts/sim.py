"""Calibrated simulation study. Synthetic users are generated in pose space
(head 6-DoF + both controllers, 60 Hz) and pushed through the exact feature /
template / scoring / decision code used on the headset (engine.py).
Population parameters are calibrated to the feature ranges measured on the
Quest pilot (data/real_windows.npz). Everything here is SIMULATED."""
import numpy as np, json, sys
from engine import extract, Template, decide

HZ = 60
SEED = 20261026


_K = np.exp(-0.5 * (np.arange(-24, 25) / 8.0) ** 2); _K /= _K.sum()   # ~0.13 s Gaussian low-pass


def ou(n, tau, sigma, rng, dt=1 / HZ):
    """Ornstein-Uhlenbeck process, low-pass filtered so it is smooth like tracked human motion."""
    a = np.exp(-dt / tau)
    x = np.zeros(n + 48)
    e = rng.normal(0, sigma * np.sqrt(1 - a * a), n + 48)
    for i in range(1, n + 48):
        x[i] = a * x[i - 1] + e[i]
    return np.convolve(x, _K, mode='same')[24:24 + n]


def person(rng):
    return dict(h=rng.uniform(1.05, 1.55), r=rng.uniform(0.15, 0.45), s=rng.uniform(0.04, 0.13),
                d=rng.uniform(0.15, 0.35), yaw_sd=rng.uniform(3, 40), yaw_tau=rng.uniform(1.0, 4.0),
                p0=rng.uniform(0, 18), p_sd=rng.uniform(2, 7), turn_rate=rng.uniform(0.03, 0.25),
                turn_amp=rng.uniform(10, 60), sway=rng.uniform(0.04, 0.30), sway_tau=rng.uniform(0.8, 3),
                hand_sd=rng.uniform(0.08, 0.22), hand_tau=rng.uniform(0.2, 0.6), trem=rng.uniform(0.00004, 0.00016))


def session_of(p, rng, day_shift=True, posture=0.0):
    """Same person on another occasion: small posture/activity changes."""
    q = dict(p)
    if day_shift:
        q['h'] = p['h'] + rng.uniform(-0.02, 0.02)
        q['r'] = p['r'] * rng.uniform(0.95, 1.05)
        q['s'] = p['s'] * rng.uniform(0.95, 1.05)
        for k in ('yaw_sd', 'p_sd', 'turn_rate', 'turn_amp', 'sway', 'hand_sd'):
            q[k] = p[k] * rng.uniform(0.8, 1.25)
        q['p0'] = p['p0'] + rng.uniform(-3, 3)
    q['h'] += posture
    return q


def motion(q, dur, rng):
    n = int(dur * HZ)
    t = np.arange(n) / HZ
    yaw = ou(n, q['yaw_tau'], q['yaw_sd'], rng)
    k = rng.poisson(q['turn_rate'] * dur)          # deliberate look-around head turns
    for _ in range(k):
        c = rng.uniform(0, dur); w = rng.uniform(0.3, 0.8); amp = q['turn_amp'] * rng.choice([-1, 1])
        yaw += amp * np.exp(-0.5 * ((t - c) / (w / 2)) ** 2)
    pitch = q['p0'] + ou(n, 1.0, q['p_sd'], rng)
    body = ou(n, 4.0, 0.4 * q['yaw_sd'], rng)        # torso yaw follows slowly
    head = np.c_[ou(n, q['sway_tau'], q['sway'], rng),
                 q['h'] + ou(n, q['sway_tau'], 0.5 * q['sway'], rng),
                 ou(n, q['sway_tau'], q['sway'], rng)] + rng.normal(0, q['trem'], (n, 3))
    y, x = np.radians(yaw) / 2, np.radians(pitch) / 2
    hrot = np.c_[np.cos(y) * np.sin(x), np.sin(y) * np.cos(x), -np.sin(y) * np.sin(x), np.cos(y) * np.cos(x)]
    by = np.radians(body)
    def hand(side, scale):
        off = np.c_[side * q['s'] + ou(n, q['hand_tau'], scale * q['hand_sd'], rng),
                    -q['d'] + ou(n, q['hand_tau'], 0.6 * scale * q['hand_sd'], rng),
                    q['r'] * (1 if side > 0 else 0.92) + ou(n, q['hand_tau'], 0.5 * scale * q['hand_sd'], rng)]
        rx = off[:, 0] * np.cos(by) + off[:, 2] * np.sin(by)
        rz = -off[:, 0] * np.sin(by) + off[:, 2] * np.cos(by)
        return head + np.c_[rx, off[:, 1], rz] + rng.normal(0, q['trem'], (n, 3))
    return t, head, hrot, hand(-1, 0.7), hand(1, 1.0)


def windows(stream, win=3.0, hop=0.5):
    t, head, hrot, L, R = stream
    W, H = int(win * HZ), int(hop * HZ)
    out, ends = [], []
    for s in range(0, len(t) - W + 1, H):
        e = s + W
        f = extract(t[s:e], head[s:e], hrot[s:e], L[s:e], R[s:e])
        if f is not None:
            out.append(f); ends.append(t[e - 1])
    return np.array(out), np.array(ends)


def concat(a, b):
    t = np.r_[a[0], a[0][-1] + 1 / HZ + b[0]]
    return (t,) + tuple(np.r_[x, y] for x, y in zip(a[1:], b[1:]))


def legacy_spoof(head, hz=HZ, thr=2.5, floor=0.35, strikes=3, refr=0.4, decay=12.0, base=90):
    """Port of SpoofDetector.cs (speed z-score vs rolling 1.8 s baseline). Returns revoke time or None."""
    sp = np.linalg.norm(np.diff(head, axis=0), axis=1) * hz
    buf, st, last, lastdec = [], 0, -1e9, 0.0
    for i, s in enumerate(sp):
        t = i / hz
        if len(buf) >= base:
            m, sd = np.mean(buf), np.std(buf)
            if sd > 1e-4 and s >= floor and abs(s - m) / sd > thr and t - last >= refr:
                st += 1; last = t; lastdec = t
                if st >= strikes:
                    return t
        buf.append(s)
        if len(buf) > base:
            buf.pop(0)
        if st > 0 and t - lastdec >= decay:
            st -= 1; lastdec = t
    return None


def run(N=40, win=3.0, seed=SEED, handovers=5, posture=0.0):
    rng = np.random.default_rng(seed)
    P = [person(rng) for _ in range(N)]
    enrol, genA, genB, streamB = [], [], [], []
    for p in P:
        e = motion(session_of(p, rng, day_shift=False), 60, rng)
        enrol.append(windows(e, win)[0])
        a = motion(session_of(p, rng, day_shift=False), 120, rng)
        genA.append(windows(a, win)[0])
        bs = motion(session_of(p, rng, day_shift=True, posture=posture), 120, rng)
        streamB.append(bs)
        genB.append(windows(bs, win)[0])
    T = [Template(E) for E in enrol]
    res = dict(N=N, win=win)
    gA = np.concatenate([T[i].score(genA[i]) for i in range(N)])
    gB = np.concatenate([T[i].score(genB[i]) for i in range(N)])
    imp = np.concatenate([T[i].score(genB[j]) for i in range(N) for j in range(N) if i != j])
    res['gA'], res['gB'], res['imp'] = gA, gB, imp
    # same-build impostor: nearest neighbour in eye height + reach
    geo = np.array([[p['h'], p['r']] for p in P]) / [0.15, 0.1]
    nn = [int(np.argsort(np.linalg.norm(geo - geo[i], axis=1))[1]) for i in range(N)]
    res['imp_nn'] = np.concatenate([T[i].score(genB[nn[i]]) for i in range(N)])
    res['per_user_gB'] = [float(T[i].score(genB[i]).mean()) for i in range(N)]
    res['P'] = P
    res['T'], res['streamB'], res['nn'] = T, streamB, nn
    return res


def eer(g, im):
    ths = np.linspace(0, 1, 2001)
    far = np.array([(im >= t).mean() for t in ths]); frr = np.array([(g < t).mean() for t in ths])
    i = np.argmin(np.abs(far - frr))
    return (far[i] + frr[i]) / 2, ths[i], ths, far, frr


def operational(res, k=4, thr=0.25, win=3.0, handovers=5, seed=SEED + 1):
    """Stream-level decisions exactly as on the headset: genuine 120 s sessions (false lockouts)
    and handover trials (30 s genuine then 30 s another user)."""
    rng = np.random.default_rng(seed)
    T, S, N = res['T'], res['streamB'], res['N']
    false_lock = 0; minutes = 0
    for i in range(N):
        sc = T[i].score(windows(S[i], win)[0])
        idx, _ = decide(sc, threshold=thr, k=k)
        false_lock += idx is not None; minutes += len(S[i][0]) / HZ / 60
    lat, det, trials = [], 0, 0
    for i in range(N):
        for j in rng.choice([x for x in range(N) if x != i], handovers, replace=False):
            g = tuple(x[:30 * HZ] for x in S[i]); m = tuple(x[:30 * HZ] for x in S[j])
            st = concat(g, m)
            W, ends = windows(st, win)
            idx, _ = decide(T[i].score(W), threshold=thr, k=k)
            trials += 1
            if idx is not None and ends[idx] > 30:
                det += 1; lat.append(ends[idx] - 30)
    return dict(false_lockouts=int(false_lock), genuine_sessions=N, genuine_minutes=float(minutes),
                trials=trials, detected=det, latency=np.array(lat))
