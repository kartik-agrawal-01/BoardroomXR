using System.Collections.Generic;
using UnityEngine;
using BoardroomXR.Identity;

namespace BoardroomXR.UI
{
    /// <summary>
    /// "In this meeting" board (v6 trust badge). Lists every participant avatar with a
    /// coloured trust ring: green verified, amber warning, orange re-checking, blue
    /// learning a posture, red locked, grey signing in.
    ///
    /// It reads only the replicated <see cref="AvatarIdentity.Trust"/> variables, so every
    /// client in the meeting renders the same board from the server's verdict - which is
    /// the point: in a collaborative room, the other people must be able to see when the
    /// person behind an avatar is no longer the one who signed in.
    ///
    /// Mounted on the left wall, facing the table. No colliders.
    /// </summary>
    public class ParticipantTrustBoard : MonoBehaviour
    {
        public float forward = 1.45f;
        public float right = -2.35f;
        public float height = 1.55f;
        public Vector2 size = new Vector2(1.05f, 0.62f);
        public int maxRows = 5;

        private const float Layer = -0.003f;

        private Transform _root;
        private readonly List<Material> _materials = new();
        private readonly List<Row> _rows = new();
        private TextMesh _footer;
        private float _nextRefresh;

        private class Row
        {
            public GameObject go;
            public Material ring, dot;
            public TextMesh name, status;
        }

        private void Update()
        {
            if (_root == null)
            {
                if (XrRigLocator.Origin == null && Camera.main == null) return;
                Build();
            }
            if (Time.unscaledTime < _nextRefresh) return;
            _nextRefresh = Time.unscaledTime + 0.25f;
            Refresh();
        }

        private void OnDestroy() => BoardroomMaterials.DestroyAll(_materials);

        private void Build()
        {
            Vector3 pos = XrRigLocator.Place(forward, right, height);
            var go = new GameObject("ParticipantTrustBoard");
            go.transform.SetParent(transform, false);
            go.transform.position = pos;
            go.transform.rotation = XrRigLocator.FacingOrigin(pos, 1.5f);
            _root = go.transform;

            SpatialUiFactory.Quad(_root, "Edge", new Vector3(0f, 0f, 0.002f), size + new Vector2(0.014f, 0.014f),
                new Color(0.30f, 0.42f, 0.55f, 0.9f), out var edge);
            _materials.Add(edge);
            SpatialUiFactory.Quad(_root, "Back", Vector3.zero, size, new Color(0.035f, 0.045f, 0.065f, 0.97f), out var back);
            _materials.Add(back);

            float halfW = size.x * 0.5f, halfH = size.y * 0.5f;
            var title = SpatialUiFactory.Text(_root, "Title", new Vector3(-halfW + 0.04f, halfH - 0.05f, Layer), 0.04f,
                new Color(0.86f, 0.92f, 1f), TextAnchor.MiddleLeft, TextAlignment.Left);
            title.text = "IN THIS MEETING";
            var sub = SpatialUiFactory.Text(_root, "Sub", new Vector3(-halfW + 0.04f, halfH - 0.095f, Layer), 0.019f,
                new Color(0.55f, 0.66f, 0.78f), TextAnchor.MiddleLeft, TextAlignment.Left);
            sub.text = "live identity check of every participant";

            for (int i = 0; i < maxRows; i++)
            {
                float y = halfH - 0.17f - i * 0.085f;
                var row = new Row { go = new GameObject("Row" + i) };
                row.go.transform.SetParent(_root, false);
                row.go.transform.localPosition = new Vector3(0f, y, 0f);

                SpatialUiFactory.Quad(row.go.transform, "Ring", new Vector3(-halfW + 0.07f, 0f, Layer * 0.5f),
                    new Vector2(0.056f, 0.056f), Color.gray, out row.ring);
                SpatialUiFactory.Quad(row.go.transform, "Dot", new Vector3(-halfW + 0.07f, 0f, Layer),
                    new Vector2(0.036f, 0.036f), new Color(0.035f, 0.045f, 0.065f, 1f), out row.dot);
                _materials.Add(row.ring);
                _materials.Add(row.dot);

                row.name = SpatialUiFactory.Text(row.go.transform, "Name", new Vector3(-halfW + 0.12f, 0.012f, Layer), 0.03f,
                    Color.white, TextAnchor.MiddleLeft, TextAlignment.Left);
                row.status = SpatialUiFactory.Text(row.go.transform, "Status", new Vector3(-halfW + 0.12f, -0.022f, Layer), 0.018f,
                    new Color(0.65f, 0.72f, 0.80f), TextAnchor.MiddleLeft, TextAlignment.Left);
                row.go.SetActive(false);
                _rows.Add(row);
            }

            _footer = SpatialUiFactory.Text(_root, "Footer", new Vector3(-halfW + 0.04f, -halfH + 0.035f, Layer), 0.016f,
                new Color(0.45f, 0.55f, 0.66f), TextAnchor.MiddleLeft, TextAlignment.Left);
            _footer.text = "Shown to everyone in the meeting  ·  decided by the server, not the wearer";
        }

        private void Refresh()
        {
            var people = FindObjectsByType<AvatarIdentity>(FindObjectsInactive.Exclude, FindObjectsSortMode.None);
            int shown = 0;
            foreach (var p in people)
            {
                if (shown >= _rows.Count) break;
                if (!p.IsSpawned) continue;
                var row = _rows[shown++];
                row.go.SetActive(true);

                string id = p.ClaimedUserIdString;
                string name = BadgeDirectory.NameFor(id);
                var level = p.TrustLevelValue;
                Color c = Colour(level);
                row.ring.color = c;
                row.name.text = string.IsNullOrEmpty(name) ? id : name;
                row.status.text = Describe(level, p.TrustPercent.Value);
                row.status.color = Color.Lerp(c, Color.white, 0.25f);
            }
            for (int i = shown; i < _rows.Count; i++) _rows[i].go.SetActive(false);

            if (shown == 0 && _rows.Count > 0)
            {
                _rows[0].go.SetActive(true);
                _rows[0].ring.color = new Color(0.4f, 0.45f, 0.5f);
                _rows[0].name.text = "Waiting for the meeting to start";
                _rows[0].status.text = "no participants connected yet";
            }
        }

        public static Color Colour(TrustLevel l) => l switch
        {
            TrustLevel.Verified => new Color(0.36f, 0.88f, 0.48f),
            TrustLevel.Warning => new Color(1f, 0.76f, 0.25f),
            TrustLevel.StepUp => new Color(1f, 0.55f, 0.18f),
            TrustLevel.Learning => new Color(0.45f, 0.75f, 1f),
            TrustLevel.Locked => new Color(1f, 0.30f, 0.28f),
            _ => new Color(0.55f, 0.60f, 0.66f),
        };

        public static string Describe(TrustLevel l, int pct) => l switch
        {
            TrustLevel.Verified => $"VERIFIED  ·  trust {pct}%",
            TrustLevel.Warning => $"MOVEMENT CHANGED  ·  trust {pct}%",
            TrustLevel.StepUp => "RE-CHECKING  ·  asked to sign again",
            TrustLevel.Learning => "VERIFIED  ·  learning a new posture",
            TrustLevel.Locked => "LOCKED OUT  ·  not the signed-in person",
            _ => "SIGNING IN",
        };
    }
}
