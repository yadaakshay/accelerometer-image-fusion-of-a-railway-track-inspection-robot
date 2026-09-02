# YOLO Railway Track Inspection Model

## Overview

This directory contains the trained YOLO model used for railway track component and defect detection in the final inspection pipeline.

## Model

Model file:

`best_v3_4class_981images.pt`

The model is used by the final dashboard pipeline to perform visual detection on the extracted RGB camera frames.

## Detection Classes

The model contains four classes:

```text
0 - Fastener
1 - Sleeper
2 - Railway Track
3 - Missing Fastener
```

## Final Inference Configuration

The final dashboard uses the following inference configuration:

| Parameter | Value |
|---|---:|
| IoU threshold | 0.30 |
| Fastener confidence | 0.05 |
| Sleeper confidence | 0.40 |
| Railway Track confidence | 0.10 |
| Missing Fastener confidence | 0.08 |

Class-specific confidence thresholds are applied to retain useful detections for components with different visual sizes and appearances.

## Visualization

The final inspection dashboard uses:

* Bounding boxes and labels for all four classes
* Segmentation masks for Fastener
* Segmentation masks for Missing Fastener
* No segmentation masks for Sleeper
* No segmentation masks for Railway Track

## Usage

The model is loaded by the final dashboard script:

`pipeline/05_dashboard_yolo.py`

Example:

```python
from ultralytics import YOLO

model = YOLO("model/best_v3_4class_981images.pt")
```

The model is then applied to the extracted RGB frames as part of the final inspection pipeline.

## Integration

The model output is combined with the spatially synchronized vibration data and vibration-event information.

```text
RGB Frame
    ↓
YOLO Model
    ↓
Fastener / Sleeper / Railway Track / Missing Fastener
    ↓
Visual Detection
    ↓
Combined with Vibration Information
    ↓
Unified Inspection Status
```

## Requirements

The model is used with the Ultralytics YOLO framework.

See the main repository `README.md` for the complete railway inspection pipeline and execution sequence.
