---
title: Staged GitHub Import — px4-uav
confidence: inferred
tags: [inbox]
sources:
  - kind: github
    ref: https://example.org/px4-uav
---

> **Status: STAGED — awaiting `career_builder` enrichment.**
> This note was created by `career_collector` from a GitHub repository. Facts are `inferred` until
> confirmed by the user. Do not use in derived documents until enriched.

## Raw Extracted Text

### README (excerpt)
> PX4 UAV Autonomy — on-board state estimation and control for RoboMaster 2023. Runs ROS 2 on
> Raspberry Pi 4, communicates with PX4 over MAVLink. EKF + PID control loop.

### Recent Commits
- feat(ekf): tune covariance for vibration noise
- perf(mavlink): batch setpoints at 100Hz
- test: add closed-loop latency benchmark

### Release v1.2.0
- Control latency: 12ms
- Hover precision: 8cm

## Extracted Facts (unconfirmed)
- Stack: ROS 2, Python, C++, PX4, MAVLink, EKF, PID
- Metrics: 12ms latency, 8cm hover error
- Team: 4 (inferred from commit authors)

## Next Steps
Run `career_builder` to confirm these facts, fill missing fields (role, competition, evidence), and
promote this to `vault/career/projects/PX4 UAV.md` with `confidence: confirmed`.
