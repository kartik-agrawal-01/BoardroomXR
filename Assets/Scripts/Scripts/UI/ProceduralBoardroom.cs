using System.Collections.Generic;
using UnityEngine;

namespace BoardroomXR.UI
{
    /// <summary>
    /// Builds a closed, furnished meeting room around the existing scene layout (v6),
    /// so the demo reads as a real corporate boardroom instead of the grey VR-template
    /// studio: four walls and a ceiling that hide the template props, carpet and a rug,
    /// a window wall with a daylight skyline, wood panelling, a conference table with
    /// chairs and table settings, a wall screen, a credenza, plants and lighting.
    ///
    /// The layout keeps clear of everything the demo needs: the PIN keypad (1.6 m
    /// ahead), the OTP token, the badge reader, the presenter console, the security
    /// doors at 2.3 m and the confidential whiteboard on the back wall.
    ///
    /// Everything is primitives placed in the measured room frame, and
    /// <b>every collider is stripped</b> - the XRI ray interactors must still reach
    /// the PIN keypad canvas and the OTP token through all of it.
    /// </summary>
    public class ProceduralBoardroom : MonoBehaviour
    {
        [Header("Room shell (measured frame: forward, right, height in metres)")]
        public float wallForward = 3.2f;      // back wall, behind the whiteboard
        public float rearForward = -1.35f;    // wall behind the user
        public float leftRight = -2.7f;       // solid wall with the participant board
        public float rightRight = 3.1f;       // window wall
        public float ceilingHeight = 2.85f;

        [Header("Conference table (kept in front of the door line at 2.3 m)")]
        public float tableForwardStart = 0.45f;
        public float tableForwardEnd = 2.12f;
        public float tableRight = 1.85f;
        public float tableWidth = 1.05f;
        public float tableTopHeight = 0.74f;

        private readonly List<Material> _materials = new();
        private Transform _root;

        // shared materials
        private Material _plaster, _plasterDark, _walnut, _walnutDark, _steel, _black, _fabric, _carpet, _rug,
                         _glass, _sky, _skyLow, _city, _ceiling, _lightPanel, _cove, _leaf, _pot, _paper, _screen;

        private void Update()
        {
            if (_root != null) return;
            if (XrRigLocator.Origin == null && Camera.main == null) return;
            Build();
        }

        private void OnDestroy() => BoardroomMaterials.DestroyAll(_materials);

        private void Build()
        {
            var go = new GameObject("ProceduralBoardroom");
            go.transform.SetParent(transform, false);
            _root = go.transform;

            MakeMaterials();
            BuildFloor();
            BuildBackWall();
            BuildSideAndRearWalls();
            BuildWindowWall();
            BuildCeiling();
            BuildTable();
            BuildChairs();
            BuildTableSettings();
            BuildWallScreen();
            BuildCredenzaAndDecor();

            // Belt and braces: nothing built here may carry a collider.
            SpatialUiFactory.StripColliders(go);
        }

        private void MakeMaterials()
        {
            _plaster = Track(BoardroomMaterials.Lit(new Color(0.80f, 0.78f, 0.74f), 0.15f));
            _plasterDark = Track(BoardroomMaterials.Lit(new Color(0.26f, 0.28f, 0.32f), 0.2f));
            _walnut = Track(BoardroomMaterials.Lit(new Color(0.33f, 0.20f, 0.12f), 0.55f));
            _walnutDark = Track(BoardroomMaterials.Lit(new Color(0.20f, 0.12f, 0.08f), 0.45f));
            _steel = Track(BoardroomMaterials.Lit(new Color(0.55f, 0.56f, 0.58f), 0.7f, 0.6f));
            _black = Track(BoardroomMaterials.Lit(new Color(0.06f, 0.06f, 0.07f), 0.5f));
            _fabric = Track(BoardroomMaterials.Lit(new Color(0.12f, 0.14f, 0.18f), 0.08f));
            _carpet = Track(BoardroomMaterials.Lit(new Color(0.30f, 0.30f, 0.32f), 0.03f));
            _rug = Track(BoardroomMaterials.Lit(new Color(0.20f, 0.24f, 0.32f), 0.04f));
            _glass = Track(BoardroomMaterials.Translucent(new Color(0.75f, 0.88f, 0.95f, 0.10f)));
            _sky = Track(BoardroomMaterials.Emissive(new Color(0.62f, 0.78f, 0.95f), 1.0f));
            _skyLow = Track(BoardroomMaterials.Emissive(new Color(0.86f, 0.90f, 0.94f), 1.0f));
            _city = Track(BoardroomMaterials.Lit(new Color(0.36f, 0.42f, 0.52f), 0.2f));
            _ceiling = Track(BoardroomMaterials.Lit(new Color(0.88f, 0.88f, 0.86f), 0.1f));
            _lightPanel = Track(BoardroomMaterials.Emissive(new Color(1f, 0.97f, 0.90f), 1.5f));
            _cove = Track(BoardroomMaterials.Emissive(new Color(1f, 0.82f, 0.58f), 1.2f));
            _leaf = Track(BoardroomMaterials.Lit(new Color(0.18f, 0.40f, 0.20f), 0.2f));
            _pot = Track(BoardroomMaterials.Lit(new Color(0.85f, 0.84f, 0.80f), 0.3f));
            _paper = Track(BoardroomMaterials.Lit(new Color(0.95f, 0.95f, 0.93f), 0.1f));
            _screen = Track(BoardroomMaterials.Emissive(new Color(0.10f, 0.20f, 0.36f), 1.0f));
        }

        // ---------------- shell ----------------

        private void BuildFloor()
        {
            float depth = wallForward - rearForward, width = rightRight - leftRight;
            float cf = (wallForward + rearForward) * 0.5f, cr = (rightRight + leftRight) * 0.5f;
            Box("Carpet", cf, cr, 0.006f, new Vector3(width, 0.012f, depth), _carpet);
            // Rug under the table, a little larger than its footprint.
            float tf = (tableForwardStart + tableForwardEnd) * 0.5f, tl = tableForwardEnd - tableForwardStart;
            Box("Rug", tf, tableRight, 0.016f, new Vector3(tableWidth + 1.6f, 0.008f, tl + 1.3f), _rug);
        }

        private void BuildBackWall()
        {
            float width = rightRight - leftRight, cr = (rightRight + leftRight) * 0.5f;
            Box("BackWall", wallForward, cr, ceilingHeight * 0.5f, new Vector3(width, ceilingHeight, 0.08f), _plasterDark);

            // Walnut slat panelling either side of the whiteboard.
            for (int side = 0; side < 2; side++)
            {
                float from = side == 0 ? leftRight + 0.15f : 1.05f;
                float to = side == 0 ? -1.05f : rightRight - 0.15f;
                for (float r = from; r <= to; r += 0.11f)
                    Box($"Slat{side}_{r:F2}", wallForward - 0.06f, r, 1.35f, new Vector3(0.05f, 2.4f, 0.04f), _walnut);
            }
            Box("BackSkirting", wallForward - 0.05f, cr, 0.05f, new Vector3(width, 0.10f, 0.03f), _walnutDark);
            Box("BackCove", wallForward - 0.07f, cr, ceilingHeight - 0.08f, new Vector3(width - 0.2f, 0.025f, 0.03f), _cove);

            // Room name above the whiteboard.
            Vector3 titlePos = XrRigLocator.Place(wallForward - 0.09f, 0f, 2.5f);
            var titleGo = new GameObject("BoardroomTitle");
            titleGo.transform.SetParent(_root, false);
            titleGo.transform.position = titlePos;
            titleGo.transform.rotation = XrRigLocator.FacingOrigin(titlePos, 1.6f);
            var title = SpatialUiFactory.Text(titleGo.transform, "Title", Vector3.zero, 0.085f, new Color(0.96f, 0.93f, 0.86f));
            title.text = "BOARDROOM";
            var sub = SpatialUiFactory.Text(titleGo.transform, "Subtitle", new Vector3(0f, -0.1f, 0f), 0.042f,
                new Color(0.95f, 0.72f, 0.35f));
            sub.text = "BOARD MEETING  ·  CONFIDENTIAL";
        }

        private void BuildSideAndRearWalls()
        {
            float depth = wallForward - rearForward, cf = (wallForward + rearForward) * 0.5f;
            float width = rightRight - leftRight, cr = (rightRight + leftRight) * 0.5f;

            // Left wall: plaster with a walnut dado rail and skirting.
            Box("LeftWall", cf, leftRight, ceilingHeight * 0.5f, new Vector3(0.08f, ceilingHeight, depth), _plaster);
            Box("LeftDado", cf, leftRight + 0.05f, 0.95f, new Vector3(0.03f, 0.05f, depth), _walnut);
            Box("LeftSkirting", cf, leftRight + 0.05f, 0.05f, new Vector3(0.03f, 0.10f, depth), _walnutDark);

            // Two framed prints on the left wall, either side of the participant board.
            Frame("PrintA", 0.25f, leftRight + 0.06f, 1.6f, new Vector2(0.55f, 0.75f), new Color(0.55f, 0.36f, 0.22f));
            Frame("PrintB", 2.85f, leftRight + 0.06f, 1.6f, new Vector2(0.45f, 0.60f), new Color(0.28f, 0.40f, 0.48f));

            // Rear wall behind the user, with a walnut door.
            Box("RearWall", rearForward, cr, ceilingHeight * 0.5f, new Vector3(width, ceilingHeight, 0.08f), _plaster);
            Box("RearSkirting", rearForward + 0.05f, cr, 0.05f, new Vector3(width, 0.10f, 0.03f), _walnutDark);
            Box("DoorFrame", rearForward + 0.05f, -1.6f, 1.08f, new Vector3(1.04f, 2.16f, 0.04f), _walnutDark);
            Box("Door", rearForward + 0.07f, -1.6f, 1.05f, new Vector3(0.92f, 2.08f, 0.03f), _walnut);
            Box("DoorHandle", rearForward + 0.10f, -1.25f, 1.02f, new Vector3(0.14f, 0.025f, 0.03f), _steel);

            // Frosted glass partition either side of the security doors (door line at 2.3 m),
            // so the doors sit in a wall: the inner boardroom is behind glass until you verify.
            const float doorLine = 2.3f;
            for (int s = 0; s < 2; s++)
            {
                float a = s == 0 ? leftRight : 1.08f, b = s == 0 ? -1.08f : rightRight;
                float mid = (a + b) * 0.5f, w = b - a;
                Box($"Partition{s}", doorLine, mid, 1.1f, new Vector3(w, 2.2f, 0.02f), _glass);
                Box($"PartitionBand{s}", doorLine, mid, 1.05f, new Vector3(w, 0.12f, 0.025f), _plaster);
                Box($"PartitionHead{s}", doorLine, mid, 2.53f, new Vector3(w, 0.66f, 0.06f), _plaster);
                for (float r = a; r <= b + 0.01f; r += w / 3f)
                    Box($"PartitionPost{s}_{r:F2}", doorLine, r, 1.1f, new Vector3(0.04f, 2.2f, 0.05f), _black);
            }
            Box("DoorHeadWall", doorLine, 0f, 2.53f, new Vector3(2.2f, 0.66f, 0.06f), _plaster);
        }

        private void BuildWindowWall()
        {
            float depth = wallForward - rearForward, cf = (wallForward + rearForward) * 0.5f;

            // Daylight beyond the glass: a bright sky band over a paler horizon and a
            // simple skyline, so the room reads as a high-floor office.
            Box("SkyUpper", cf, rightRight + 0.6f, 2.05f, new Vector3(0.02f, 1.8f, depth + 2f), _sky);
            Box("SkyLower", cf, rightRight + 0.6f, 0.75f, new Vector3(0.02f, 1.0f, depth + 2f), _skyLow);
            float[] towers = { 0.9f, 1.4f, 0.7f, 1.7f, 1.1f, 1.5f, 0.8f, 1.25f, 1.6f, 0.95f };
            for (int i = 0; i < towers.Length; i++)
            {
                float f = rearForward - 0.6f + i * (depth + 1.2f) / towers.Length;
                Box($"Tower{i}", f, rightRight + 0.55f, 0.55f + towers[i] * 0.5f, new Vector3(0.02f, towers[i], 0.36f), _city);
            }

            // Sill, head and mullions.
            Box("WindowSill", cf, rightRight, 0.42f, new Vector3(0.16f, 0.84f, depth), _plaster);
            Box("WindowHead", cf, rightRight, 2.72f, new Vector3(0.16f, 0.26f, depth), _plaster);
            Box("WindowGlass", cf, rightRight - 0.01f, 1.57f, new Vector3(0.01f, 2.04f, depth), _glass);
            int mullions = 6;
            for (int i = 0; i <= mullions; i++)
            {
                float f = rearForward + i * depth / mullions;
                Box($"Mullion{i}", f, rightRight - 0.02f, 1.57f, new Vector3(0.06f, 2.04f, 0.05f), _black);
            }
            Box("Transom", cf, rightRight - 0.02f, 2.2f, new Vector3(0.05f, 0.04f, depth), _black);
        }

        private void BuildCeiling()
        {
            float depth = wallForward - rearForward, cf = (wallForward + rearForward) * 0.5f;
            float width = rightRight - leftRight, cr = (rightRight + leftRight) * 0.5f;
            Box("Ceiling", cf, cr, ceilingHeight + 0.03f, new Vector3(width, 0.04f, depth), _ceiling);

            // Recessed light panels in two rows: one over the user, one over the table.
            for (int i = 0; i < 3; i++)
            {
                float f = 0.1f + i * 1.1f;
                Box($"LightA{i}", f, -0.4f, ceilingHeight, new Vector3(0.6f, 0.02f, 0.6f), _lightPanel);
                Box($"LightB{i}", f, tableRight, ceilingHeight, new Vector3(0.6f, 0.02f, 0.6f), _lightPanel);
            }
            // A linear pendant over the table.
            float tf = (tableForwardStart + tableForwardEnd) * 0.5f, tl = tableForwardEnd - tableForwardStart;
            Box("PendantBody", tf, tableRight, 2.15f, new Vector3(0.08f, 0.04f, tl * 0.75f), _black);
            Box("PendantGlow", tf, tableRight, 2.125f, new Vector3(0.06f, 0.01f, tl * 0.73f), _cove);
            Box("PendantWireA", tf - tl * 0.3f, tableRight, 2.5f, new Vector3(0.006f, 0.7f, 0.006f), _black);
            Box("PendantWireB", tf + tl * 0.3f, tableRight, 2.5f, new Vector3(0.006f, 0.7f, 0.006f), _black);
        }

        // ---------------- furniture ----------------

        private void BuildTable()
        {
            float tl = tableForwardEnd - tableForwardStart, tf = (tableForwardStart + tableForwardEnd) * 0.5f;
            float straight = tl - tableWidth;   // rounded ends: half-cylinders of the table's width

            Box("TableTop", tf, tableRight, tableTopHeight, new Vector3(tableWidth, 0.05f, straight), _walnut);
            Cyl("TableEndA", tf - straight * 0.5f, tableRight, tableTopHeight, tableWidth, 0.05f, _walnut);
            Cyl("TableEndB", tf + straight * 0.5f, tableRight, tableTopHeight, tableWidth, 0.05f, _walnut);
            Box("TableEdge", tf, tableRight, tableTopHeight - 0.035f, new Vector3(tableWidth - 0.04f, 0.02f, straight), _walnutDark);

            // Two pedestal legs on steel feet, and a cable trough down the middle.
            for (int i = 0; i < 2; i++)
            {
                float f = tf + (i == 0 ? -1f : 1f) * straight * 0.32f;
                Box($"TableLeg{i}", f, tableRight, tableTopHeight * 0.5f, new Vector3(0.18f, tableTopHeight - 0.05f, 0.18f), _walnutDark);
                Box($"TableFoot{i}", f, tableRight, 0.02f, new Vector3(0.62f, 0.03f, 0.30f), _steel);
            }
            Box("CableTrough", tf, tableRight, tableTopHeight + 0.027f, new Vector3(0.16f, 0.006f, straight * 0.6f), _black);
        }

        private void BuildChairs()
        {
            float tl = tableForwardEnd - tableForwardStart, tf = (tableForwardStart + tableForwardEnd) * 0.5f;
            float side = tableWidth * 0.5f + 0.38f;
            // Two along each long side, one at the near end (facing the back wall).
            float[] along = { -0.38f, 0.38f };
            int n = 0;
            foreach (float a in along)
            {
                Chair($"Chair{n++}", tf + a, tableRight - side, Vector3.right);
                Chair($"Chair{n++}", tf + a, tableRight + side, Vector3.left);
            }
            Chair($"Chair{n}", tableForwardStart - 0.42f, tableRight, Vector3.forward);
        }

        /// <summary>An executive chair: five-star base, gas lift, seat, high back and arms.</summary>
        private void Chair(string name, float f, float r, Vector3 facingLocal)
        {
            // Build the chair under its own pivot so it can be turned to face the table.
            var pivot = new GameObject(name);
            pivot.transform.SetParent(_root, false);
            pivot.transform.position = XrRigLocator.Place(f, r, 0f);
            Vector3 worldFacing = XrRigLocator.Forward * facingLocal.z + XrRigLocator.Right * facingLocal.x;
            pivot.transform.rotation = Quaternion.LookRotation(worldFacing, Vector3.up);
            var p = pivot.transform;

            for (int i = 0; i < 5; i++)
            {
                var spoke = Part(p, "Spoke" + i, new Vector3(0f, 0.04f, 0f), new Vector3(0.05f, 0.03f, 0.56f), _black);
                spoke.transform.localRotation = Quaternion.Euler(0f, i * 72f, 0f);
            }
            Part(p, "Lift", new Vector3(0f, 0.25f, 0f), new Vector3(0.05f, 0.40f, 0.05f), _steel);
            Part(p, "Seat", new Vector3(0f, 0.47f, 0f), new Vector3(0.50f, 0.08f, 0.48f), _fabric);
            var back = Part(p, "Back", new Vector3(0f, 0.86f, -0.26f), new Vector3(0.48f, 0.70f, 0.07f), _fabric);
            back.transform.localRotation = Quaternion.Euler(-8f, 0f, 0f);
            Part(p, "Headrest", new Vector3(0f, 1.25f, -0.31f), new Vector3(0.34f, 0.12f, 0.07f), _fabric);
            for (int s = -1; s <= 1; s += 2)
            {
                Part(p, "ArmPost" + s, new Vector3(0.27f * s, 0.58f, -0.02f), new Vector3(0.03f, 0.18f, 0.03f), _steel);
                Part(p, "ArmPad" + s, new Vector3(0.27f * s, 0.68f, 0.0f), new Vector3(0.06f, 0.025f, 0.30f), _black);
            }
        }

        private void BuildTableSettings()
        {
            float tf = (tableForwardStart + tableForwardEnd) * 0.5f;
            float edge = tableWidth * 0.5f - 0.2f;
            float top = tableTopHeight + 0.03f;
            float[] along = { -0.38f, 0.38f };
            int n = 0;
            foreach (float a in along)
            {
                for (int s = -1; s <= 1; s += 2)
                {
                    float r = tableRight + s * edge;
                    Box($"Notepad{n}", tf + a, r, top, new Vector3(0.16f, 0.008f, 0.22f), _paper);
                    Box($"Pen{n}", tf + a + 0.02f, r + s * -0.11f, top + 0.004f, new Vector3(0.008f, 0.008f, 0.14f), _black);
                    Cyl($"Glass{n}", tf + a + 0.16f, r + s * -0.05f, top + 0.05f, 0.065f, 0.11f, _glass);
                    n++;
                }
            }
            // Closed laptop at the head of the table and a conference speaker in the middle.
            Box("Laptop", tableForwardStart + 0.12f, tableRight, top + 0.01f, new Vector3(0.32f, 0.018f, 0.22f), _steel);
            Cyl("Speaker", tf, tableRight, top + 0.02f, 0.2f, 0.04f, _black);
            Cyl("SpeakerRing", tf, tableRight, top + 0.042f, 0.12f, 0.004f, _cove);
        }

        private void BuildWallScreen()
        {
            // A wall-mounted display on the back wall, to the right of the whiteboard.
            float r = 2.1f;
            Box("ScreenBezel", wallForward - 0.08f, r, 1.55f, new Vector3(1.45f, 0.84f, 0.04f), _black);
            Box("ScreenFace", wallForward - 0.105f, r, 1.55f, new Vector3(1.38f, 0.77f, 0.01f), _screen);

            Vector3 pos = XrRigLocator.Place(wallForward - 0.12f, r, 1.55f);
            var go = new GameObject("ScreenText");
            go.transform.SetParent(_root, false);
            go.transform.position = pos;
            go.transform.rotation = XrRigLocator.FacingOrigin(pos, 1.6f);
            var t = SpatialUiFactory.Text(go.transform, "Agenda", new Vector3(-0.62f, 0.3f, 0f), 0.045f,
                new Color(0.9f, 0.95f, 1f), TextAnchor.UpperLeft, TextAlignment.Left);
            t.text = "<b>Q3 Board Review</b>\n\n1  Results and outlook\n2  Acquisition proposal\n3  Security incident report\n4  AOB";
        }

        private void BuildCredenzaAndDecor()
        {
            // Low walnut credenza along the left wall, under the participant board.
            float l = leftRight + 0.25f;
            Box("Credenza", 1.4f, l, 0.36f, new Vector3(0.42f, 0.72f, 1.5f), _walnut);
            Box("CredenzaTop", 1.4f, l, 0.73f, new Vector3(0.45f, 0.025f, 1.54f), _walnutDark);
            for (int i = 0; i < 3; i++)
                Box($"CredenzaDoorLine{i}", 0.9f + i * 0.5f, l + 0.215f, 0.36f, new Vector3(0.005f, 0.6f, 0.005f), _walnutDark);
            Cyl("Jug", 1.05f, l, 0.85f, 0.11f, 0.22f, _glass);
            Box("Books", 1.75f, l, 0.79f, new Vector3(0.2f, 0.1f, 0.3f), _plasterDark);

            Plant("PlantBackLeft", wallForward - 0.35f, leftRight + 0.35f, 1.1f);
            Plant("PlantBackRight", wallForward - 0.35f, rightRight - 0.4f, 1.0f);
            Plant("PlantRear", rearForward + 0.35f, rightRight - 0.4f, 0.9f);
        }

        private void Plant(string name, float f, float r, float height)
        {
            Cyl(name + "Pot", f, r, 0.22f, 0.38f, 0.44f, _pot);
            Cyl(name + "Soil", f, r, 0.445f, 0.34f, 0.01f, _walnutDark);
            Box(name + "Stem", f, r, 0.44f + height * 0.3f, new Vector3(0.03f, height * 0.6f, 0.03f), _walnutDark);
            float[,] blobs = { { 0f, 0f, 0.62f, 0.42f }, { 0.12f, 0.08f, 0.8f, 0.34f }, { -0.1f, -0.06f, 0.85f, 0.32f }, { 0.02f, 0.1f, 1.0f, 0.26f } };
            for (int i = 0; i < blobs.GetLength(0); i++)
            {
                Vector3 pos = XrRigLocator.Place(f + blobs[i, 0], r + blobs[i, 1], 0.44f + blobs[i, 2] * height * 0.75f);
                float d = blobs[i, 3] * (0.6f + 0.4f * height);
                var leaf = SpatialUiFactory.Primitive(PrimitiveType.Sphere, _root, name + "Leaves" + i, Vector3.zero,
                    new Vector3(d, d * 0.85f, d), Quaternion.identity, _leaf);
                leaf.transform.position = pos;
            }
        }

        private void Frame(string name, float f, float r, float h, Vector2 size, Color art)
        {
            var artMat = Track(BoardroomMaterials.Lit(art, 0.2f));
            Box(name + "Frame", f, r, h, new Vector3(0.03f, size.y + 0.06f, size.x + 0.06f), _black);
            Box(name + "Mount", f, r + 0.017f, h, new Vector3(0.005f, size.y, size.x), _paper);
            Box(name + "Art", f, r + 0.021f, h, new Vector3(0.005f, size.y * 0.72f, size.x * 0.72f), artMat);
        }

        // ---------------- helpers ----------------

        /// <summary>
        /// A box in the measured room frame. <paramref name="size"/> is (across, up,
        /// along-forward) in metres, so layout reads the same way the room was measured.
        /// </summary>
        private GameObject Box(string name, float forward, float right, float height, Vector3 size, Material material)
        {
            Vector3 pos = XrRigLocator.Place(forward, right, height);
            var go = SpatialUiFactory.Primitive(PrimitiveType.Cube, _root, name, Vector3.zero,
                new Vector3(size.x, size.y, size.z), Quaternion.identity, material);
            go.transform.position = pos;
            // Local +Z points along the user's forward, +X along their right.
            go.transform.rotation = Quaternion.LookRotation(XrRigLocator.Forward, Vector3.up);
            return go;
        }

        /// <summary>An upright cylinder of the given diameter and height, centred at (forward, right, height).</summary>
        private GameObject Cyl(string name, float forward, float right, float height, float diameter, float tall, Material material)
        {
            Vector3 pos = XrRigLocator.Place(forward, right, height);
            // Unity's cylinder is 2 units tall, so y scale is half the height.
            var go = SpatialUiFactory.Primitive(PrimitiveType.Cylinder, _root, name, Vector3.zero,
                new Vector3(diameter, tall * 0.5f, diameter), Quaternion.identity, material);
            go.transform.position = pos;
            return go;
        }

        /// <summary>A cube in a local pivot's space (for things that are rotated as a whole, like chairs).</summary>
        private GameObject Part(Transform parent, string name, Vector3 localPos, Vector3 size, Material material) =>
            SpatialUiFactory.Primitive(PrimitiveType.Cube, parent, name, localPos, size, Quaternion.identity, material);

        private Material Track(Material m)
        {
            if (m != null) _materials.Add(m);
            return m;
        }
    }
}
