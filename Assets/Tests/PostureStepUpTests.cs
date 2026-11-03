using System;
using System.Collections.Generic;
using NUnit.Framework;
using UnityEngine;
using BoardroomXR.Biometrics;

namespace BoardroomXR.Tests
{
    /// <summary>
    /// v6 posture step-up, exercised on the engine directly with scripted motion:
    /// a genuine user who sits down is asked for the signature instead of being locked
    /// out, learns a seated profile and is recognised seated on the next login; an
    /// impostor who fails or ignores the step-up is still locked out; switching the
    /// step-up off restores the v5 direct lockout.
    /// </summary>
    public class PostureStepUpTests
    {
        private float _t;
        private System.Random _rng;

        [SetUp]
        public void SetUp()
        {
            _t = 0f;
            _rng = new System.Random(7);
        }

        private void Feed(ContinuousBiometricEngine e, float secs, bool seated, bool impostor = false, float impostorEye = 1.90f)
        {
            float eye = impostor ? impostorEye : seated ? 1.20f : 1.65f;
            float reach = impostor ? 0.55f : seated ? 0.26f : 0.35f;
            float sway = impostor ? 0.06f : seated ? 0.012f : 0.02f;
            float pitch = seated ? -16f : -5f;
            float drop = seated ? -0.30f : -0.45f;
            int n = (int)(secs * 60);
            for (int i = 0; i < n; i++)
            {
                _t += 1f / 60f;
                float ph = _t * 1.3f, j = (float)(_rng.NextDouble() - 0.5) * 0.004f;
                var head = new Vector3(Mathf.Sin(ph) * sway, eye + Mathf.Sin(ph * 0.7f) * 0.01f + j, Mathf.Cos(ph * 0.9f) * sway * 0.5f);
                e.Push(new KinematicSample
                {
                    t = _t,
                    headPos = head,
                    headRot = Quaternion.Euler(pitch + Mathf.Sin(ph) * 3f, 0f, 0f),
                    leftPos = head + new Vector3(-0.25f, drop, reach + Mathf.Sin(ph * 1.7f) * 0.05f),
                    rightPos = head + new Vector3(0.25f, drop, reach + Mathf.Cos(ph * 1.5f) * 0.06f),
                    hasLeft = true,
                    hasRight = true,
                });
            }
        }

        private static ContinuousBiometricEngine Make(List<string> log, bool stepUp = true)
        {
            var c = new BiometricConfig { enrolSeconds = 30f, postureStepUp = stepUp };
            c.ApplyPreset(BiometricPreset.Balanced);
            var e = new ContinuousBiometricEngine(c);
            e.OnLockout += r => log.Add("lockout:" + r);
            e.OnStepUpRequested += () => log.Add("stepup");
            e.OnPostureLearned += _ => log.Add("posture");
            return e;
        }

        [Test]
        public void GenuineUserSittingDown_IsAskedForSignature_ThenLearnsSeatedPosture()
        {
            var log = new List<string>();
            var e = Make(log);
            e.Begin("TEST-STEPUP", null, _t);
            Feed(e, 32f, seated: false);
            Assert.AreEqual(BiometricState.Verified, e.State, "standing enrolment");

            Feed(e, 8f, seated: true);
            Assert.IsTrue(e.StepUpPending, "sitting down asks for the signature");
            Assert.AreNotEqual(BiometricState.LockedOut, e.State, "no lockout while waiting");

            e.ResolveStepUp(true, _t, "test");
            Assert.IsTrue(e.IsPostureEnrolling, "posture learning starts");
            Feed(e, 11f, seated: true);
            Assert.AreEqual(1, e.PostureTemplates.Count, "one seated profile learned");

            Feed(e, 15f, seated: true);
            Assert.AreEqual(BiometricState.Verified, e.State, "verified seated");
            Assert.AreEqual(1, e.LastMatchedTemplate, "matched the seated profile");

            Feed(e, 15f, seated: false);
            Assert.AreEqual(BiometricState.Verified, e.State, "verified standing again");
            Assert.AreEqual(1, log.FindAll(x => x == "stepup").Count, "only one step-up");

            // Next login with both profiles: seated straight away is accepted.
            var log2 = new List<string>();
            var e2 = Make(log2);
            e2.Begin("TEST-STEPUP", e.Template, e.PostureTemplates, _t);
            Feed(e2, 15f, seated: true);
            Assert.AreEqual(BiometricState.Verified, e2.State);
            Assert.IsFalse(log2.Contains("stepup"));
        }

        [Test]
        public void PostureTemplate_LearnedWhileStill_KeepsTheMainTemplatesSpread()
        {
            // 30 Oct headset run: a posture learned while standing still had spreads of
            // 1-60% of the main template's, so normal movement afterwards scored ~0.
            var log = new List<string>();
            var e = Make(log);
            e.Begin("TEST-STEPUP", null, _t);
            Feed(e, 32f, seated: false);
            Feed(e, 8f, seated: true);
            e.ResolveStepUp(true, _t, "test");
            Feed(e, 11f, seated: true);
            Assert.AreEqual(1, e.PostureTemplates.Count);
            var posture = e.PostureTemplates[0];
            for (int i = 0; i < KinematicFeatures.Count; i++)
                Assert.GreaterOrEqual(posture.sd[i], e.Template.sd[i] - 1e-6f, $"feature {i} spread narrower than the main template");
        }

        [Test]
        public void Impostor_FailingTheSignature_IsLockedOut()
        {
            var log = new List<string>();
            var e = Make(log);
            e.Begin("TEST-STEPUP", null, _t);
            Feed(e, 32f, seated: false);
            Feed(e, 8f, seated: false, impostor: true);
            Assert.IsTrue(e.StepUpPending);
            e.ResolveStepUp(false, _t, "gesture 0.31");
            Assert.AreEqual(BiometricState.LockedOut, e.State);
            Assert.IsTrue(log.Exists(x => x.StartsWith("lockout:posture step-up failed")));
        }

        [Test]
        public void SimilarHeightImpostor_IsLockedOutWithoutAStepUp()
        {
            // Knowing the signature must not be enough: with no real posture change
            // (eye height within 20 cm of a known posture) no step-up is offered.
            var log = new List<string>();
            var e = Make(log);
            e.Begin("TEST-STEPUP", null, _t);
            Feed(e, 32f, seated: false);
            Feed(e, 10f, seated: false, impostor: true, impostorEye: 1.72f);
            Assert.AreEqual(BiometricState.LockedOut, e.State);
            Assert.IsFalse(log.Contains("stepup"), "no signature prompt for a non-posture mismatch");
            Assert.IsTrue(log.Exists(x => x.Contains("no posture change")));
        }

        [Test]
        public void UnansweredStepUp_LocksOutAfterTheDeadline()
        {
            var log = new List<string>();
            var e = Make(log);
            e.Begin("TEST-STEPUP", null, _t);
            Feed(e, 32f, seated: false);
            Feed(e, 8f, seated: false, impostor: true);
            Assert.IsTrue(e.StepUpPending);
            Feed(e, e.Config.stepUpSeconds + 1f, seated: false, impostor: true);
            Assert.AreEqual(BiometricState.LockedOut, e.State);
            Assert.IsTrue(log.Exists(x => x.Contains("not answered")));
        }

        [Test]
        public void StepUpOff_KeepsTheDirectLockout()
        {
            var log = new List<string>();
            var e = Make(log, stepUp: false);
            e.Begin("TEST-STEPUP", null, _t);
            Feed(e, 32f, seated: false);
            Feed(e, 8f, seated: false, impostor: true);
            Assert.AreEqual(BiometricState.LockedOut, e.State);
            Assert.IsFalse(log.Contains("stepup"));
        }

        [Test]
        public void PostureTemplates_SaveLoadAndDelete()
        {
            var log = new List<string>();
            var e = Make(log);
            e.Begin("TEST-STEPUP", null, _t);
            Feed(e, 32f, seated: false);
            Feed(e, 8f, seated: true);
            e.ResolveStepUp(true, _t, "test");
            Feed(e, 11f, seated: true);
            Assert.AreEqual(1, e.PostureTemplates.Count);

            e.Template.Save();
            BiometricTemplate.SavePostures("TEST-STEPUP", e.PostureTemplates);
            Assert.AreEqual(1, BiometricTemplate.LoadPostures("TEST-STEPUP", 2).Count);
            Assert.AreEqual("TEST-STEPUP", e.PostureTemplates[0].userId, "in-memory id unchanged");

            int removed = BiometricTemplate.DeleteAllFor("TEST-STEPUP");
            Assert.GreaterOrEqual(removed, 2);
            Assert.AreEqual(0, BiometricTemplate.LoadPostures("TEST-STEPUP", 2).Count);
            Assert.IsNull(BiometricTemplate.Load("TEST-STEPUP"));
        }
    }
}
