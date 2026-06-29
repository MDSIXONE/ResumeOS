---
entity_type: project
title: ROS Navigation — Mobile Robot SLAM
id: ros-nav
status: completed
timeline:
  start: 2022-09-01
  end: 2023-02-01
  ongoing: false
role: Lead
team_size: 3
company: null
competition: null
stack:
  hardware: [TurtleBot3, RPLidar]
  software: [ROS 2, Nav2, Cartographer]
  protocol: []
  algorithm: [SLAM, A*]
  dataset: []
metrics:
  - metric: map accuracy
    value: "96%"
    context: 20x20m room
contribution: Built the SLAM pipeline and tuned Nav2 costmaps for obstacle avoidance.
ats_keywords: [ROS 2, Nav2, SLAM, Cartographer, mobile robot]
interview_questions:
  - How did you tune Cartographer's loop closure?
  - Why Nav2 over a custom planner?
evidence:
  github: https://example.org/ros-nav
  paper: null
  patent: null
  presentation: null
  images: []
  demo: null
related: [px4-uav]
tags: [robotics, slam, navigation]
confidence: confirmed
sources:
  - kind: github
    ref: https://example.org/ros-nav
$resumeos:
  schema_version: "1.0.0"
---

## Background
A course project extending into a lab deployment: a mobile robot that maps and navigates an
unknown indoor environment.

## Problem
Existing SLAM configs drifted in feature-poor corridors; Nav2 default costmaps got stuck near
glass walls.

## Goal
Achieve >95% map accuracy and reliable point-to-point navigation in a 20x20m room.

## Architecture
TurtleBot3 + RPLidar → Cartographer SLAM → Nav2 with a custom costmap layer for transparent
obstacles.

## Workflow
Bag recordings → Cartographer tuning → costmap layer → navigation benchmarks.

## Challenges
Glass-wall false-negatives; loop closure in long corridors; CPU budget on the robot.

## Solutions
Added a ray-tracing costmap layer treating lidar-through-glass as occupied; tuned loop-closure
submap spacing.

## Metrics
- Map accuracy: 96% (20x20m room).

## Contribution
Built the SLAM pipeline and the custom costmap layer; led the 3-person team.

## Lessons Learned
Costmap design matters as much as the planner; bag-recorded regression tests save weeks.

## STAR Story
**Situation:** The lab robot could not navigate glass-walled corridors. **Task:** Lead a 3-person
team to fix SLAM drift and navigation failures. **Action:** Built a Cartographer SLAM pipeline and
a custom Nav2 costmap layer for transparent obstacles. **Result:** 96% map accuracy and reliable
navigation in a 20x20m room.

## Future Improvements
Add visual-inertial fusion for texture-poor areas; benchmark against SLAM Toolbox.

## Related Notes
- [[PX4 UAV]]
