---
entity_type: project
title: PX4 UAV Autonomy
id: px4-uav
status: completed
timeline:
  start: 2023-03-01
  end: 2023-08-01
  ongoing: false
role: Embedded & Algorithm Lead
team_size: 4
company: null
competition: "[[RoboMaster 2023]]"
stack:
  hardware: [PX4, "Raspberry Pi 4"]
  software: [ROS 2, Python, C++]
  protocol: [MAVLink]
  algorithm: [PID, EKF]
  dataset: []
metrics:
  - metric: control latency
    value: 12ms
    context: closed-loop
  - metric: position error
    value: 8cm
    context: hover
contribution: Designed EKF-based state estimation and PID controller; led integration of MAVLink communications.
ats_keywords: [PX4, ROS 2, EKF, PID, embedded]
interview_questions:
  - How did you tune the EKF covariance matrices?
  - Why MAVLink over a custom protocol?
evidence:
  github: https://example.org/px4-uav
  paper: null
  patent: null
  presentation: null
  images: []
  demo: null
related: [ros-nav, robomaster-2023]
tags: [robotics, drone, embedded]
confidence: confirmed
sources:
  - kind: github
    ref: https://example.org/px4-uav
  - kind: certificate
    ref: RoboMaster 2023 certificate
$resumeos:
  schema_version: "1.0.0"
---

## Background
As part of the university robotics team preparing for RoboMaster 2023, we needed an autonomous UAV
capable of stable hover and waypoint navigation under competition constraints.

## Problem
The stock PX4 stack lacked the tight-loop state estimation needed for our custom frame. Off-board
control introduced unacceptable latency.

## Goal
Build an on-board autonomy module with sub-15ms control latency and sub-10cm hover precision.

## Architecture
Raspberry Pi 4 ran ROS 2 nodes for state estimation and control; a PX4 flight controller handled
low-level actuation over MAVLink. EKF fused IMU + optical-flow; PID closed the loop.

## Workflow
Sensor calibration → EKF tuning → PID gain scheduling → MAVLink bridge → field tests.

## Challenges
Vibration noise corrupted optical-flow; MAVLink timing jitter; limited compute on Pi 4.

## Solutions
Added a notch filter on IMU data; batched MAVLink setpoints at 100Hz; profiled ROS 2 nodes to keep
the control loop under 12ms.

## Metrics
- Control latency: 12ms (closed-loop).
- Position error: 8cm (hover).

## Contribution
Designed the EKF state estimator, tuned PID gains, and led the 4-person integration effort.

## Lessons Learned
State estimation quality dominates control performance; protocol timing matters as much as
algorithm choice.

## STAR Story
**Situation:** RoboMaster 2023 required autonomous hover within 10cm. **Task:** I led a 4-person
team to build the on-board autonomy stack. **Action:** I designed an EKF estimator and PID
controller over MAVLink on ROS 2, tuning for vibration and timing jitter. **Result:** We achieved
12ms control latency and 8cm hover precision, reaching the national finals.

## Future Improvements
Move to EKF3 with GPS fusion for outdoor waypoints; port control node to C++ for lower latency.

## Related Notes
- [[ROS Navigation]]
- [[RoboMaster 2023]]
- [[National Robotics Championship 2023]]
