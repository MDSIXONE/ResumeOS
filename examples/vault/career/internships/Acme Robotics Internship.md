---
entity_type: internship
title: Perception Intern
id: acme-internship-2023
company: Acme Robotics
team: Autonomy
timeline:
  start: 2023-06-01
  end: 2023-09-01
  ongoing: false
role: Perception Intern
mentor: Dr. Smith
stack:
  hardware: [Jetson Nano]
  software: [ROS 2, PyTorch]
  protocol: []
  algorithm: [YOLO, Kalman]
  dataset: [internal]
contribution: Ported YOLOv8 to an edge device and built a perception pipeline for field testing.
metrics:
  - metric: detection FPS
    value: "30"
    context: edge
outcome: Shipped the perception module to a field test.
offer: true
related: [yolo-detect, px4-uav]
evidence:
  url: null
  image: []
tags: [internship, perception, robotics]
confidence: confirmed
sources:
  - kind: manual
    ref: internship report
$resumeos:
  schema_version: "1.0.0"
---

## Summary
Summer 2023 internship on the Autonomy team at Acme Robotics. Ported YOLOv8 to an edge device and
built a perception pipeline that shipped to a field test. Received a return offer.

## Contribution
- Ported YOLOv8 to Jetson Nano with optimized NMS.
- Built a ROS 2 perception node feeding a Kalman-filter tracker.
- Delivered 30 FPS on edge hardware in field test.

## Outcome
Module shipped to field test; return offer extended.
