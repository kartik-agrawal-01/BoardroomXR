# BoardroomXR paper package

- `BoardroomXR_paper.pdf`: local two-column preview of the paper.
- `paper_ieee.tex` + `body.tex` + `figs/`: IEEE conference source. Upload these to Overleaf
  (New Project > Upload) and compile `paper_ieee.tex`; Overleaf ships IEEEtran.

## Data provenance (keep these separate)
- REAL, pilot (26 Oct 2026): `data/headset_logs/`, `data/real_*.json|npz`.
- REAL, team study (27 Oct 2026, the 4 authors, 11 sessions with deliberately varied behaviour):
  `data/day2/` (score CSVs and MFA session logs from the Quest), `data/day2_*.json|npz|pkl` (derived).
  Session-to-author mapping: `data/day2_people.json` (P01-P04). Author-aware analysis: `scripts/day2_people.py`, `day2_people2.py`.
- SIMULATED, idealised: `data/sim_*.json|npz` (40 synthetic users, seed 20261026).
- SIMULATED, re-calibrated to the headset sessions: `data/field_*.json` (see paper Sec. VI-E).
Never report simulated numbers as human trials.

## Scripts (`scripts/`)
- `engine.py`: Python port of the deployed C# verifier.
- Pilot: `parse_real.py`, `real_windows.py`, `real_analysis.py`.
- Field study: `day2_mfa.py` (entry gate), `day2_bio.py` (sessions, cross-score matrix),
  `day2_eer.py` (EERs, bootstrap, feature groups), `day2_explore.py` (protocol C, averaging, cohort
  normalisation), `replay.py` (trace-driven handover replay per preset).
- Idealised simulation: `sim.py`, `experiments.py`, `op_sweep.py`.
- Field-calibrated simulation: `sim_field.py`, `calib_field2.py` (calibration search),
  `field_experiments.py` (remedies), `field_replay.py` (validation on lockout behaviour).
- Figures: `figs.py` (shared style), `figs2.py` (all figures used in this version).

Reproduce (field study + new figures):
`cd scripts && python3 day2_mfa.py && python3 day2_bio.py && python3 day2_eer.py && python3 replay.py && python3 calib_field2.py && python3 field_experiments.py && python3 field_replay.py && python3 figs2.py`

## Note for the GitHub copy
Raw on-device logs are not duplicated here; the per-session window CSVs are in the group's
telemetry/real_participants/ folder. Only derived results (data/*.json) are included.
