"""Line-for-line Python port of the BoardroomXR continuous biometric engine
(KinematicFeatures.cs, BiometricTemplate.cs, ContinuousBiometricEngine.cs)."""
import numpy as np

NAMES = ["head_speed_mean", "head_speed_sd", "head_angvel_mean", "head_angvel_sd", "head_accel_mean",
         "head_jerk_mean", "rhand_speed_mean", "rhand_speed_sd", "lhand_speed_mean", "lhand_speed_sd",
         "head_rhand_dist_mean", "head_rhand_dist_sd", "head_lhand_dist_mean", "head_height_mean",
         "head_pitch_mean", "hand_span_mean"]
ABS_FLOOR = np.array([0.02, 0.02, 2, 2, 0.1, 1, 0.03, 0.03, 0.03, 0.03, 0.01, 0.005, 0.01, 0.015, 1.5, 0.02])
ZCLAMP = 6.0


def quat_angle_deg(q1, q2):
    d = np.abs(np.sum(q1 * q2, axis=-1)).clip(0, 1)
    return np.degrees(2 * np.arccos(d))


def signed_pitch(q):
    # Unity eulerAngles.x for quaternion (x,y,z,w); positive = looking down
    x, y, z, w = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    s = 2 * (w * x - y * z)
    return np.degrees(np.arcsin(np.clip(s, -1, 1)))


def extract(t, head, hrot, left, right):
    """t:(n,), head/left/right:(n,3), hrot:(n,4) xyzw. Returns 16 features or None."""
    n = len(t)
    if n < 6:
        return None
    dt = np.diff(t)
    ok = dt > 1e-4
    v = np.diff(head, axis=0)[ok] / dt[ok, None]
    tv = t[1:][ok]
    if len(v) < 4:
        return None
    hs = np.linalg.norm(v, axis=1)
    ha = quat_angle_deg(hrot[:-1][ok], hrot[1:][ok]) / dt[ok]
    rs = np.linalg.norm(np.diff(right, axis=0)[ok], axis=1) / dt[ok]
    ls = np.linalg.norm(np.diff(left, axis=0)[ok], axis=1) / dt[ok]
    dtv = np.diff(tv)
    a = np.diff(v, axis=0) / dtv[:, None]
    ta = tv[1:]
    j = np.diff(a, axis=0) / np.diff(ta)[:, None] if len(a) > 1 else np.zeros((0, 3))
    dR = np.linalg.norm(head - right, axis=1)
    f = np.empty(16)
    f[0], f[1] = hs.mean(), hs.std()
    f[2], f[3] = ha.mean(), ha.std()
    f[4] = np.linalg.norm(a, axis=1).mean() if len(a) else 0
    f[5] = np.linalg.norm(j, axis=1).mean() if len(j) else 0
    f[6], f[7] = rs.mean(), rs.std()
    f[8], f[9] = ls.mean(), ls.std()
    f[10], f[11] = dR.mean(), dR.std()
    f[12] = np.linalg.norm(head - left, axis=1).mean()
    f[13] = head[:, 1].mean()
    f[14] = signed_pitch(hrot).mean()
    f[15] = np.linalg.norm(left - right, axis=1).mean()
    return f


class Template:
    def __init__(self, windows):
        W = np.asarray(windows)
        self.n = len(W)
        self.mean = W.mean(0)
        s = W.std(0, ddof=1) if len(W) > 1 else np.zeros(16)
        floor = np.maximum(ABS_FLOOR, 0.02 * np.abs(self.mean))
        self.sd = np.maximum(s, floor)

    def score(self, f, mask=None):
        z = np.clip((np.asarray(f) - self.mean) / self.sd, -ZCLAMP, ZCLAMP)
        if mask is not None:
            z = z[..., mask]
        d2 = (z ** 2).mean(-1)
        return np.exp(-0.5 * d2)


def build(windows):
    return Template(windows) if len(windows) >= 5 else None


def decide(scores, threshold=0.25, smoothing=0.35, k=4, hop=0.5, grace=2.0, t0=0.0):
    """Run the engine's smoothing + consecutive-violation rule over a score stream.
    Returns (lockout_index or None, smoothed array)."""
    sm, viol, s_prev = [], 0, None
    for i, s in enumerate(scores):
        s_prev = s if s_prev is None else smoothing * s + (1 - smoothing) * s_prev
        sm.append(s_prev)
        t = t0 + i * hop
        if s_prev < threshold and t >= grace:
            viol += 1
            if viol >= k:
                return i, np.array(sm)
        else:
            viol = 0
    return None, np.array(sm)
