using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.InputSystem;
using BoardroomXR.Auth;
using BoardroomXR.Biometrics;
using BoardroomXR.Identity;
using BoardroomXR.Logging;

namespace BoardroomXR.UI
{
    /// <summary>
    /// Privacy panel (v6). One screen that says, in plain language, what this system
    /// keeps about the wearer, where it is kept and who sees it - with live file counts
    /// for the current badge and a "Delete my data" button that really deletes it.
    ///
    /// Every line here is a statement about how this build actually behaves; if the
    /// code changes, change the text. Hidden by default; the right controller's B
    /// button (or the presenter console) shows it. No colliders.
    /// </summary>
    public class PrivacyPanel : MonoBehaviour
    {
        public static PrivacyPanel Instance { get; private set; }

        public float forward = 1.3f;
        public float right = 0f;
        public float height = 1.85f;
        public Vector2 size = new Vector2(0.78f, 0.62f);

        private const float Layer = -0.003f;

        private Transform _root;
        private readonly List<Material> _materials = new();
        private TextMesh _body, _counts, _status;
        private SpatialButton _csvButton;
        private InputAction _toggle;
        private bool _togglePressed;
        private bool _visible;
        private float _nextRefresh;

        private void Awake()
        {
            Instance = this;
            _toggle = new InputAction("Privacy/Toggle", InputActionType.Value, expectedControlType: "Axis");
            _toggle.AddBinding("<XRController>{RightHand}/secondaryButton");
        }

        private void OnEnable() => _toggle?.Enable();
        private void OnDisable() => _toggle?.Disable();

        private void OnDestroy()
        {
            _toggle?.Dispose();
            BoardroomMaterials.DestroyAll(_materials);
            if (Instance == this) Instance = null;
        }

        public bool Visible => _visible;

        public void SetVisible(bool on)
        {
            _visible = on;
            if (_root != null) _root.gameObject.SetActive(on);
            if (on) Refresh();
            SessionLogger.LogGlobal($"[Privacy] Panel {(on ? "shown" : "hidden")}.");
        }

        private void Update()
        {
            if (_root == null)
            {
                if (XrRigLocator.Origin == null && Camera.main == null) return;
                Build();
                _root.gameObject.SetActive(_visible);
            }

            float v = _toggle != null ? _toggle.ReadValue<float>() : 0f;
            bool pressed = v > 0.5f;
            if (pressed && !_togglePressed) SetVisible(!_visible);
            _togglePressed = pressed;

            if (_visible && Time.unscaledTime >= _nextRefresh)
            {
                _nextRefresh = Time.unscaledTime + 1f;
                Refresh();
            }
        }

        private void Build()
        {
            Vector3 pos = XrRigLocator.Place(forward, right, height);
            var go = new GameObject("PrivacyPanel");
            go.transform.SetParent(transform, false);
            go.transform.position = pos;
            go.transform.rotation = XrRigLocator.FacingOrigin(pos, 1.5f);
            _root = go.transform;

            SpatialUiFactory.Quad(_root, "Edge", new Vector3(0f, 0f, 0.002f), size + new Vector2(0.012f, 0.012f),
                new Color(0.32f, 0.62f, 0.52f, 0.9f), out var edge);
            _materials.Add(edge);
            SpatialUiFactory.Quad(_root, "Back", Vector3.zero, size, new Color(0.035f, 0.05f, 0.055f, 0.97f), out var back);
            _materials.Add(back);

            float halfW = size.x * 0.5f, halfH = size.y * 0.5f;
            var title = SpatialUiFactory.Text(_root, "Title", new Vector3(-halfW + 0.03f, halfH - 0.04f, Layer), 0.03f,
                new Color(0.75f, 1f, 0.88f), TextAnchor.MiddleLeft, TextAlignment.Left);
            title.text = "YOUR PRIVACY";

            _body = SpatialUiFactory.Text(_root, "Body", new Vector3(-halfW + 0.03f, halfH - 0.08f, Layer), 0.0145f,
                new Color(0.86f, 0.90f, 0.94f), TextAnchor.UpperLeft, TextAlignment.Left);
            _body.text =
                "<b>Movement profile</b>: averages and spreads of 16 movement\n" +
                "features (speeds, distances, eye height). Kept on this headset only.\n" +
                "<b>Raw head and hand positions</b>: held in memory for the last 3 s\n" +
                "to score you, then dropped. Saved only: a short enrolment clip for\n" +
                "the mimicry demo, and raw telemetry if the presenter presses Record.\n" +
                "<b>Air signature</b>: kept on this headset. <b>PIN</b>: checked against\n" +
                "a salted hash, never logged.\n" +
                "<b>Other people in the meeting</b> see only: verified or not, and\n" +
                "your trust colour.\n" +
                "<b>Presenter laptop</b>: live scores over the USB cable for this demo.\n" +
                "Nothing is uploaded to the internet.";

            _counts = SpatialUiFactory.Text(_root, "Counts", new Vector3(-halfW + 0.03f, -halfH + 0.14f, Layer), 0.0145f,
                new Color(0.95f, 0.85f, 0.55f), TextAnchor.MiddleLeft, TextAlignment.Left);

            var bsize = new Vector2(0.23f, 0.05f);
            var del = Button("privacy_delete", "Delete my data", new Vector3(-halfW + 0.03f + bsize.x * 0.5f, -halfH + 0.075f, Layer), bsize, DeleteMine);
            del.normalColor = new Color(0.34f, 0.08f, 0.10f, 0.95f);
            del.hoverColor = new Color(0.58f, 0.13f, 0.15f, 0.97f);
            del.ApplyColor();
            _csvButton = Button("privacy_csv", "Research log: ON", new Vector3(0f, -halfH + 0.075f, Layer), bsize, ToggleCsv);
            Button("privacy_close", "Close  [B]", new Vector3(halfW - 0.03f - bsize.x * 0.5f, -halfH + 0.075f, Layer), bsize,
                () => SetVisible(false));

            _status = SpatialUiFactory.Text(_root, "Status", new Vector3(-halfW + 0.03f, -halfH + 0.025f, Layer), 0.0135f,
                new Color(0.6f, 0.8f, 0.7f), TextAnchor.MiddleLeft, TextAlignment.Left);
            _status.text = "";
        }

        private SpatialButton Button(string id, string caption, Vector3 localPos, Vector2 bsize, System.Action onClick)
        {
            var go = new GameObject("Btn_" + id);
            go.transform.SetParent(_root, false);
            go.transform.localPosition = localPos;
            var b = go.AddComponent<SpatialButton>();
            b.size = bsize;
            b.id = id;
            SpatialUiFactory.Quad(go.transform, "Face", Vector3.zero, bsize, b.normalColor, out var face);
            b.BindFace(face);  // the button owns and destroys its face material
            var label = SpatialUiFactory.Text(go.transform, "Caption", new Vector3(0f, 0f, Layer), 0.015f, Color.white);
            label.text = caption;
            b.OnClicked += _ => onClick();
            return b;
        }

        private static string CurrentUser()
        {
            var auth = ContinuousBiometricAuthenticator.Instance;
            if (auth != null && auth.CurrentUserId != "-") return auth.CurrentUserId;
            return BadgeSwitchService.CurrentBadgeId ?? SystemInfoIdentityStub.GetLocalClaimedId();
        }

        private void Refresh()
        {
            if (_counts == null) return;
            string user = CurrentUser();
            var auth = ContinuousBiometricAuthenticator.Instance;

            int profiles = 0;
            if (File.Exists(BiometricTemplate.PathFor(user))) profiles++;
            int postures = BiometricTemplate.LoadPostures(user, 8).Count;
            bool signature = GestureTemplateStore.HasTemplate(user);
            bool clip = File.Exists(MimicryRecording.PathFor(user));
            int logs = 0;
            try
            {
                string dir = Path.Combine(Application.persistentDataPath, "BiometricLogs");
                string safe = user;
                foreach (char c in Path.GetInvalidFileNameChars()) safe = safe.Replace(c, '_');
                if (Directory.Exists(dir)) logs = Directory.GetFiles(dir, $"scores_{safe}_*.csv").Length;
            }
            catch { }

            _counts.text =
                $"Stored now for {BadgeDirectory.NameFor(user)} ({user}):  profile {profiles}  ·  posture profiles {postures}  ·  " +
                $"signature {(signature ? 1 : 0)}\nmotion clip {(clip ? 1 : 0)}  ·  research score logs {logs}";

            if (_csvButton != null && auth != null)
            {
                _csvButton.isActive = auth.writeScoreCsv;
                var cap = _csvButton.GetComponentInChildren<TextMesh>();
                if (cap != null) cap.text = auth.writeScoreCsv ? "Research log: ON" : "Research log: OFF";
                _csvButton.ApplyColor();
            }
        }

        private void DeleteMine()
        {
            var auth = ContinuousBiometricAuthenticator.Instance;
            string user = CurrentUser();
            int removed = auth != null ? auth.DeleteAllDataFor(user) : 0;
            _status.text = $"Deleted {removed} file(s) for {BadgeDirectory.NameFor(user)}. Next login starts fresh.";
            Refresh();
        }

        private void ToggleCsv()
        {
            var auth = ContinuousBiometricAuthenticator.Instance;
            if (auth == null) return;
            auth.writeScoreCsv = !auth.writeScoreCsv;
            BioEventLog.Emit("research_log", auth.CurrentUserId, auth.writeScoreCsv ? "enabled" : "disabled");
            _status.text = auth.writeScoreCsv
                ? "Research score logging ON from the next session."
                : "Research score logging OFF from the next session.";
            Refresh();
        }
    }
}
