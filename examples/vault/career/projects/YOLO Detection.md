---
entity_type: project
title: Real-Time YOLO Object Detection on Edge
id: yolo-detect
status: completed
timeline:
  start: 2024-01-01
  end: 2024-04-01
  ongoing: false
role: Solo
team_size: 1
company: null
competition: null
stack:
  hardware: [Jetson Nano]
  software: [PyTorch, YOLOv8, OpenCV]
  protocol: []
  algorithm: [YOLO, NMS]
  dataset: [COCO subset]
metrics:
  - metric: mAP
    value: "0.87"
    context: val
  - metric: FPS
    value: "42"
    context: Jetson Nano
contribution: Trained, pruned, and deployed a YOLOv8 detector to Jetson Nano with optimized NMS.
ats_keywords: [PyTorch, YOLOv8, object detection, edge, Jetson, NMS]
interview_questions:
  - How did you optimize NMS for the edge?
  - What pruning strategy did you use?
evidence:
  github: https://example.org/yolo-detect
  paper: null
  patent: null
  presentation: null
  images: []
  demo: null
related: [bci]
tags: [cv, detection, edge]
confidence: confirmed
sources:
  - kind: github
    ref: https://example.org/yolo-detect
$resumeos:
  schema_version: "1.0.0"
---

## Background
A personal project to deploy real-time object detection on a low-power edge device for a robotics
application.

## Problem
Stock YOLOv8 ran at 12 FPS on Jetson Nano — too slow for real-time use.

## Goal
Achieve >40 FPS with mAP >0.85 on a COCO subset, on Jetson Nano.

## Architecture
PyTorch training → channel pruning → ONNX export → optimized NMS inference on Nano.

## Workflow
Dataset curation → training → pruning → export → benchmark → iterate.

## Challenges
Pruning hurt small-object accuracy; NMS was a bottleneck on ARM.

## Solutions
Selective channel pruning preserving small-object heads; a fused NMS kernel cut post-processing
from 18ms to 4ms.

## Metrics
- mAP: 0.87 (val).
- FPS: 42 (Jetson Nano).

## Contribution
Solo: training, pruning, edge deployment, and NMS optimization.

## Lessons Learned
Post-processing optimization often beats model shrinking for edge FPS.

## STAR Story
**Situation:** Edge robotics needed real-time detection but YOLOv8 ran at 12 FPS on Jetson Nano.
**Task:** As a solo project, reach >40 FPS with mAP >0.85. **Action:** I trained YOLOv8, applied
selective channel pruning, and wrote a fused NMS kernel. **Result:** 0.87 mAP at 42 FPS on Jetson
Nano.

## Future Improvements
Try TensorRT INT8 quantization for a further 2x speedup.

## Related Notes
- [[Brain Computer Interface]]
