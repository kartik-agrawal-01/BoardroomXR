# IVRAR Group 13: BoardroomXR

Continuous behavioural biometric authentication in collaborative VR

**Course:** Immersive Virtual Reality & Augmented Reality (IVRAR, 702TG0C003), AY 2026–27, Semester V
**Institution:** SVKM's NMIMS MPSTME, Mumbai
**Team:** Kartik Agrawal (I001), Soha Chand (I007), Atharv Dixit (I013), Ojaswi Gondalia (I019)
**LinkedIn video:** https://lnkd.in/p/d_G32T8Q
**Presented:** Guide-to-Grade Industry Jury, 31 Oct 2026, AR/VR Lab, MPSTME
**Origin:** built as Group 13's capstone for the IVRAR course. The graded submission lives in the course repository, [sunny-nanade/NMIMS-MPSTME-IVRAR-2026](https://github.com/sunny-nanade/NMIMS-MPSTME-IVRAR-2026) (folder `Group_13_Kartik_Soha_Atharv_Ojaswi`). This repository is the team's standalone copy of the full Unity project.

---

## 1. The problem in one paragraph

Logging in to a VR meeting is a one-time check. Once you are in, nobody checks again. If you take the headset off and someone else puts it on, they become "you" in the meeting: same name, same avatar, same access to confidential material. In a collaborative enterprise room (a board meeting, a design review, a negotiation) the other participants cannot tell that the person behind your avatar has changed. BoardroomXR asks a simple question: can the headset keep checking who is wearing it, the whole time, from the way they move their head and hands?

## 2. Authorised research question

> "How can continuous behavioral biometric authentication leveraging head and hand kinematic telemetry achieve equal error rates (EER) below 5% against avatar identity-spoofing in collaborative VR enterprise environments?"

**Our honest answer, from our own headset data:** not with free-use head and hand movement alone. On real people we measured 17.2% to 30.3% EER. Our idealised simulation predicted 4.7%, and we keep that number only as a labelled simulation. The main cause we found is posture (sitting vs standing), and version 6 of the app is our engineering response to it.

---

## 3. What the system does, step by step

1. **The visitor walks into an antechamber** in front of glass security doors.
2. **Multi-factor login (server-authoritative).** All three factors are checked by the host, not the client.
   - PIN on a floating keypad (salted SHA-256, never logged).
   - 3D air signature: hold the trigger and draw a gesture in the air. Enrolment takes 3 strokes; acceptance threshold 0.65.
   - 6-digit one-time code (TOTP) read off a virtual hardware token.
3. **The doors open** and the user enters the boardroom.
4. **Movement enrolment (30 s).** The system learns how this person moves: 16 features from the head and both controllers.
5. **Continuous verification.** Every 0.5 s it scores the last 3 s of movement against the person's profile.
   - Green: verified. Amber: movement does not match. After k low windows in a row: lockout.
6. **Lockout.** The host revokes verification, the confidential whiteboard is hidden, the doors close, a red tint fills the view and the user must log in again with all three factors.
7. **Everyone in the room sees it.** The "In this meeting" board shows every participant's trust colour, decided by the server.

## 4. How the biometric engine works

| Item | Value |
|---|---|
| Sampling | Head + both controllers, 60 Hz |
| Window | 3 s, new score every 0.5 s |
| Features | 16 kinematic features (speeds, distances, hand reach, head pitch, eye height and others) |
| Profile | Mean and spread (SD, with a floor) per feature |
| Score | S = exp(−0.5 · mean z²), z clamped at ±6, smoothed (EMA 0.35) |
| Presets | Strict 0.25 / k=4 · **Balanced 0.15 / k=6 (default)** · Relaxed 0.10 / k=8 |
| Adaptation | Profile updates slowly, only while the user is trusted |

Main code: `Assets/Scripts/Scripts/Biometrics/ContinuousBiometricEngine.cs` (I001) and `KinematicFeatures.cs` (I013).

---

## 5. Who built what

| Member | Declared role | What they built and will demo |
|---|---|---|
| Kartik Agrawal (I001) | Biometric Authentication Lead | The continuous biometric engine: scoring, presets, lockout logic, adaptive profile and the v6 posture step-up |
| Soha Chand (I007) | XR Systems Architect | The VR boardroom and system flow: Netcode host/client set-up, MFA entry gate, doors, trust board, head-up display and in-room panels |
| Atharv Dixit (I013) | Kinematic Telemetry Specialist | Telemetry capture at 60 Hz and the 16-feature extractor; the on-device logging that produced our data set |
| Ojaswi Gondalia (I019) | Security QA & Threat Analyst | Threat model and attack tests (handover, mimicry, signature forgery), the team study analysis and the error-rate results |

---

## 6. What we tested and what we found

### Who and when
- The four team members (P01–P04), 11 sessions on 27 Oct 2026 (S01–S11), on a Meta Quest 2, after a 14-session pilot on 26 Oct.
- In each session the member deliberately moved differently, to stand in for a different user. This is a team study, not a study of independent users: **N = 4**.

### Results
| Check | Result |
|---|---|
| Owner signature login | 11 of 11 passed first time (mean score 0.896) |
| Forged signature (a member drawing another member's gesture) | 0 of 15 accepted (best forgery 0.574) |
| Median full login time | 31.4 s |
| Movement enrolment | 11 of 11 completed |
| Deliberate behaviour change locked out | 9 of 9, 7 of them within 2.5 s of the first warning |
| Window-level EER between different people | **17.2%** (interleaved) to **30.3%** (end of session) |
| Per-session EER | mean 25.4%, SD 17.4%, median 20.0% |
| Body geometry features only | 20.7% |
| Motion dynamics only | 48.0% |
| Old speed-threshold detector | would have wrongly revoked all 11 genuine sessions |

### The key finding: posture
A member's own second session, recorded in a different posture, scored like a stranger (0.168 vs 0.171). Eye height ranged from 1.06–1.22 m seated to 1.36–1.56 m standing. At matched posture the same person scored higher than others (0.36 vs 0.29, only 6 pairs). In plain words: the system was recognising "sitting" and "standing" more than it was recognising people.

### Simulation (labelled, not human data)
- Idealised simulator: 40 synthetic users, EER 4.7%.
- Simulator calibrated to our field data reproduces our real results; the best remedies reach about 15%, never below 5%.

### Limits we state openly
- N = 4, all team members, one headset, two days.
- People of similar height in the same posture are hard to separate.
- Sub-5% EER was met only in simulation.

---

## 7. Improvements, version by version

### v1–v4 (Oct 2026): the base system
- VR boardroom, three-factor login, continuous verifier, lockout consequences.
- Removed the course starter's fake numbers (a claimed N = 50 study with EER 4.12% and SUS 88.4 that never happened) and its synthetic data files.

### v5 (28 Oct): explainable and demo-ready
- Live trust panel that says in plain language *why* a score dropped (for example "hands held lower than usual").
- Employee badges, so several people can enrol on one headset.
- Laptop dashboard over USB and a one-click run script with automatic log capture.
- Mimicry attack demo: a "ghost" replays the owner's recorded motion to show what a copy attack looks like.

### v6 (30 Oct): fixes driven by our own finding
| Improvement | Why |
|---|---|
| **Posture step-up** | Our data showed sitting down looked like a different person. Now, instead of locking a genuine user out, the system asks "Is it still you?" and gives 15 s to draw the air signature. Pass: it learns the new posture in 10 s (up to 2 extra posture profiles). Fail or no answer: lockout. |
| **Trust badge visible to others** | Trust level (verified, warning, re-checking, learning, locked) is replicated from the server, so every participant sees who is verified on the "In this meeting" board. |
| **Controller vibration** | The controllers buzz as an early warning before a lockout. |
| **Panic gesture** | Drawing the signature backwards still logs in, but raises a silent duress alert that only the security dashboard shows. |
| **Privacy panel** (right controller B) | States in plain words what is stored, where, and who sees it, with live file counts and a working "Delete my data" button. |
| **Real meeting room** | Closed room with walls, window wall, glass partition, racetrack table with five chairs, wall screen and furniture. |
| **Recovery scripts** | One-click .bat files for install, restart, new-user wipe, reconnect, logs, screenshots, rollback and headset fixes. |

v6 was confirmed on the headset on 30 Oct: the step-up passed at 0.89 and a seated posture was learned.

### v6.1 (30 Oct): fixes from that headset test
| Fix | Why |
|---|---|
| **Head-up display always on top** | It was hidden behind the room's panels. It now draws over everything, on a dark backing plate. |
| **Posture profile spread widened** | A posture learned while standing still was too tight, so normal movement afterwards scored near zero. Replaying the real session went from 1 unwanted prompt to none. |
| **Step-up only for a real posture change** | Security fix. Before, an intruder who knew the signature could keep re-signing and stay in. Now the signature is offered only if eye height has changed by at least 20 cm from every known posture. Otherwise it is a straight lockout. |

Automated tests: 22 of 22 pass in Unity (including 7 posture step-up tests, one of them a similar-height impostor who knows the signature and is still locked out).

---

## 8. Real-world value and next step

- **Cost:** runs on the headset itself; no extra sensors, cameras or hardware.
- **Privacy:** only feature averages and spreads are stored, on the headset. Raw head and hand positions are held for 3 s and dropped. Nothing is uploaded.
- **Integration:** the engine is plain C# with no dependency on our room, so it can sit inside any Unity meeting app built on Netcode.
- **Next step:** a pilot with at least 15 outside users of varied heights, each recorded seated and standing, to test whether posture profiles bring real-world EER down, followed by a conference paper.

---

## 9. Repository map

| Path | What is in it |
|---|---|
| `Assets/Scripts/Scripts/Auth` | PIN, air signature, TOTP and the MFA coordinator |
| `Assets/Scripts/Scripts/Biometrics` | Engine, 16 features, profiles, logging, mimicry recording |
| `Assets/Scripts/Scripts/Identity` | Avatar identity, trust replication, badges |
| `Assets/Scripts/Scripts/Network` | Host bootstrap, auth relay, access gate, laptop dashboard |
| `Assets/Scripts/Scripts/UI` | Meeting room, head-up display, trust board, privacy panel, presenter console |
| `Assets/Tests` | 22 play-mode tests (incl. 7 posture step-up tests) |
| `Assets/Editor` | One-click build menu and the offline evaluation runner |
| `EXPO/` | Install, restart, wipe, log-pull, screenshot, rollback and recovery scripts for demo day |
| `BUILD_AND_TEST_v6.bat` | Runs every test, then builds the Quest APK |
| `telemetry/real_participants/` | Per-session window scores (S01–S11, people coded P01–P04) and the plot script |
| `docs/paper/` | Research paper (IEEE format), LaTeX source, analysis scripts and data |
| `docs/figures/` | Result figures |

## 10. Build and run

You need Unity **6000.5.4f1** with Android Build Support, and a Meta Quest 2 or 3 in developer mode.

1. Clone the repo (`git lfs install` first, so images download).
2. Open the folder in Unity Hub. The first import takes a while.
3. Either use the menu **BoardroomXR > Build Quest APK (v6)**, or close Unity and run `BUILD_AND_TEST_v6.bat`, which runs the tests and then builds.
4. Plug in the headset and run `EXPO\1_INSTALL_v6.bat`.
5. In the headset: pick a badge at the badge wall, enter the PIN, draw your signature with the trigger held, enter the code from the token, then move naturally for 30 s.

A ready-built APK (v6.1) is attached to this repository's **Releases**. Builds are never committed to git.

## 11. Verified literature (DOIs checked at source)

| # | Reference | Venue | DOI |
|---|---|---|---|
| 1 | Pfeuffer et al., "Behavioural Biometrics in VR: Identifying People from Body Motion and Relations in Virtual Reality" | ACM CHI 2019 | 10.1145/3290605.3300340 |
| 2 | Miller et al., "Personal identifiability of user tracking data during observation of 360-degree VR video" | Scientific Reports 2020 | 10.1038/s41598-020-74486-y |
| 3 | Miller, Banerjee, Banerjee, "Temporal Effects in Motion Behavior for VR Biometrics" | IEEE VR 2022 | 10.1109/VR51125.2022.00076 |
| 4 | Chen, Xin, Phoha, "SSPRA: A Robust Approach to Continuous Authentication Amidst Real-World Adversarial Challenges" | IEEE TBIOM 2024 | 10.1109/TBIOM.2024.3369590 |
| 5 | Li, Banerjee, Banerjee, "Real or fake motion: protecting VR behavioral authentication systems against motion forecasting attacks" | Frontiers in VR 2026 | 10.3389/frvir.2026.1766672 |
| 6 | Gyreyiri, Shukla, "Head Movement Biometrics for Continuous Authentication in Virtual Reality" | ACM VRST 2025 | 10.1145/3756884.3768408 |
| Std | ISO/IEC 19795-1:2021, Biometric performance testing and reporting | ISO/IEC | iso.org/standard/73515.html |

## 12. AI use

AI tools (Anthropic Claude) were used for implementation, analysis and drafting. Errors we caught are logged in dossier Section 5.1. Among them: Claude's simulation suggested the 5% target was met, while real sessions gave 17–30%; and the starter README's N = 50 / EER 4.12% study did not exist.

