---
entity_type: project
title: EEG Signal Classification — Brain-Computer Interface
id: bci
status: active
timeline:
  start: 2023-09-01
  end: null
  ongoing: true
role: Research Assistant
team_size: 2
company: Example University
competition: null
stack:
  hardware: [OpenBCI Cyton]
  software: [Python, MNE, scikit-learn]
  protocol: []
  algorithm: [CSP, SVM]
  dataset: [BCI Competition IV-2a]
metrics:
  - metric: accuracy
    value: "91%"
    context: 8-class motor imagery
contribution: Implemented CSP feature extraction and SVM classification pipeline; ran 8-class experiments.
ats_keywords: [EEG, BCI, CSP, SVM, MNE, signal processing]
interview_questions:
  - Why CSP over raw band power?
  - How did you handle inter-subject variance?
evidence:
  github: null
  paper: in-prep
  patent: null
  presentation: null
  images: []
  demo: null
related: [yolo-detect, eeg-classification]
tags: [bci, eeg, research]
confidence: confirmed
sources:
  - kind: paper
    ref: in-prep manuscript
$resumeos:
  schema_version: "1.0.0"
---

## Background
A lab project under my advisor to classify 8-class motor-imagery EEG signals for a BCI spelling
interface.

## Problem
8-class classification is harder than the typical 2-4 class BCI; inter-subject variance is high.

## Goal
Achieve >90% accuracy on 8-class motor imagery with a lightweight pipeline suitable for real-time
use.

## Architecture
OpenBCI Cyton acquisition → MNE preprocessing → CSP features → SVM classifier.

## Workflow
Data collection → bandpass filtering → CSP → SVM → cross-validation → subject adaptation.

## Challenges
Low SNR of EEG; small per-subject dataset; CSP sensitivity to artifact contamination.

## Solutions
Artifact rejection via ICA; per-subject CSP re-fitting; RBF-SVM with grid search.

## Metrics
- Accuracy: 91% (8-class motor imagery).

## Contribution
Implemented the CSP + SVM pipeline and ran all 8-class experiments.

## Lessons Learned
Feature engineering still beats deep learning on small EEG datasets; per-subject calibration is
non-negotiable.

## STAR Story
**Situation:** A BCI spelling interface needed 8-class motor-imagery classification above 90%.
**Task:** As research assistant, build the classification pipeline. **Action:** I implemented CSP
feature extraction and an SVM classifier with per-subject calibration. **Result:** 91% accuracy on
8-class motor imagery, feeding an in-prep manuscript.

## Future Improvements
Try deep learning (EEGNet) once more per-subject data is collected.

## Related Notes
- [[EEG Signal Classification]]
- [[YOLO Detection]]
