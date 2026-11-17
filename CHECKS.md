# Project Verification Checks

| Phase | Check Description | Status | Evidence / Notes |
|---|---|---|---|
| Phase 0 | All required files/folders exist | PASS | `.gitignore`, `LICENSE`, `requirements.txt`, `README.md`, `PROGRESS.md`, `CHECKS.md`, `data/README.md`, `notebooks/`, `results/figures/`, `results/tables/` verified |
| Phase 0 | Git status shows no data file staged | PASS | `git status` verifies raw data files in `data/` remain untracked and unstaged |
| Phase 0 | Initial git commit and first push | PASS | Initial commit b1f0f50 pushed successfully to origin/main; no data files tracked |
| Phase 1 | Timestamps parsed correctly in every file | PASS | Format `%d-%m-%Y %H:%M` for P1 Gen, `%Y-%m-%d %H:%M:%S` for P1 Wtr and P2 files parsed without error |
| Phase 1 | Merge row loss reported and under 5% | PASS | Plant 1 loss: 0.0058% (4 rows); Plant 2 loss: 0.0000% (0 rows) |
| Phase 1 | No duplicate (timestamp, inverter) pairs | PASS | 0 duplicate pairs found in Plant 1 and Plant 2 generation datasets |
| Phase 1 | Irradiation never negative | PASS | Verified min irradiation is 0.0 in both weather datasets |
| Phase 2 | Power near zero when irradiation near zero | PASS | Mean AC power <= 0.22 kW when irradiation <= 0.01 kW/m² (>99% zero) |
| Phase 2 | Every figure file saved and non-empty | PASS | `fig1` (300 KB), `fig2` (438 KB), `fig3` (97 KB), `fig4` (109 KB) saved and verified |
