# telemetry/

| Path | What it is | Human data? |
|---|---|---|
| `real_participants/` | Main headset study, 27-Oct-2026: 11 sessions (S01–S11) by the 4 team members (P01–P04) on a Meta Quest 2. Per-window scores and 16 features, session summary, gesture attempts, and `make_section4_plots.py`, which regenerates every Section 4 number and plot. | Yes (team members) |
| `real_device_data/` | Pilot, 26-Oct-2026: device event log excerpt from the first build. | Yes (team) |
| `automated_test_runs/` | Unity PlayMode / editor regression runs with scripted motion (15 runs). Software tests, not people. | No |
| `analyse_headset_logs.py`, `extract_device_events.py` | Parsers for logs pulled from the headset. | – |
| `sus_calculator.py`, `nasa_tlx_calculator.py`, `kennedy_ssq_calculator.py`, `test_evaluation_tools.py` | Questionnaire scoring tools from the course starter kit. | – |

No simulated data is stored in this folder. The simulation studies are in `docs/paper/` and are labelled as simulation there.
