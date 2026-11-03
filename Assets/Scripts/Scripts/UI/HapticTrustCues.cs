using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.XR;
using BoardroomXR.Biometrics;

namespace BoardroomXR.UI
{
    /// <summary>
    /// Controller vibration as an early warning (v6). The wearer feels the system's
    /// doubt before anything is taken away:
    ///   - a light double tap when the score first drops into Warning,
    ///   - a slightly stronger tap for each further low window,
    ///   - a long pulse every 2 s while the posture step-up waits for the signature,
    ///   - one strong buzz on lockout,
    ///   - a soft tick when trust recovers.
    /// Runs where the biometric engine runs (the headset is the host), so the pulses
    /// go to the controllers of the person actually wearing it.
    /// </summary>
    public class HapticTrustCues : MonoBehaviour
    {
        public bool cuesEnabled = true;

        private BiometricState _lastState = BiometricState.Idle;
        private int _lastViolations;
        private float _nextStepUpPulse;

        private void Update()
        {
            var e = ContinuousBiometricAuthenticator.Instance != null ? ContinuousBiometricAuthenticator.Instance.Engine : null;
            if (e == null || !cuesEnabled) return;

            if (e.State != _lastState)
            {
                if (e.State == BiometricState.Warning) { Pulse(0.35f, 0.08f); Pulse(0.35f, 0.08f, 0.15f); }
                else if (e.State == BiometricState.LockedOut) Pulse(1f, 0.6f);
                else if (e.State == BiometricState.Verified && _lastState == BiometricState.Warning) Pulse(0.15f, 0.05f);
                _lastState = e.State;
            }

            if (e.State == BiometricState.Warning && !e.StepUpPending && e.Violations > _lastViolations && _lastViolations > 0)
                Pulse(Mathf.Clamp01(0.3f + 0.1f * e.Violations), 0.07f);
            _lastViolations = e.Violations;

            if (e.StepUpPending && Time.unscaledTime >= _nextStepUpPulse)
            {
                Pulse(0.6f, 0.25f);
                _nextStepUpPulse = Time.unscaledTime + 2f;
            }
        }

        private void Pulse(float amplitude, float seconds, float delay)
        {
            if (delay <= 0f) { Pulse(amplitude, seconds); return; }
            StartCoroutine(Delayed(amplitude, seconds, delay));
        }

        private System.Collections.IEnumerator Delayed(float amplitude, float seconds, float delay)
        {
            yield return new WaitForSecondsRealtime(delay);
            Pulse(amplitude, seconds);
        }

        /// <summary>Vibrates both controllers. Safe to call with no controllers connected.</summary>
        public static void Pulse(float amplitude, float seconds)
        {
            amplitude = Mathf.Clamp01(amplitude);
            bool sent = false;
            try
            {
                foreach (var device in InputSystem.devices)
                {
                    if (device is XRControllerWithRumble rumble)
                    {
                        rumble.SendImpulse(amplitude, seconds);
                        sent = true;
                    }
                }
            }
            catch (System.Exception ex) { Debug.LogWarning($"[Haptics] Input System impulse failed: {ex.Message}"); }

            if (sent) return;

            // Fallback: the XR input subsystem path.
            try
            {
                foreach (var node in new[] { UnityEngine.XR.XRNode.LeftHand, UnityEngine.XR.XRNode.RightHand })
                {
                    var dev = UnityEngine.XR.InputDevices.GetDeviceAtXRNode(node);
                    if (dev.isValid && dev.TryGetHapticCapabilities(out var caps) && caps.supportsImpulse)
                        dev.SendHapticImpulse(0u, amplitude, seconds);
                }
            }
            catch (System.Exception ex) { Debug.LogWarning($"[Haptics] XR impulse failed: {ex.Message}"); }
        }
    }
}
