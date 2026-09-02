# Integrated Railway Track Inspection Pipeline

## Overview

This project implements an integrated railway track inspection pipeline that combines RGB video, vibration measurements, and track-position information.

The system uses robot odometry to estimate the spatial position of camera frames and vibration measurements. A calibrated constant camera-to-sensor spatial offset is then used to associate each camera frame with the nearest vibration measurement in the spatial domain.

The synchronized vibration data is analyzed to identify unusually high-vibration events, while a four-class YOLO model is used to detect railway track components and missing fasteners.

The final output is a 1280 × 720 landscape inspection dashboard containing:

* RGB camera view
* Track position
* Frame-level vibration value
* YOLO component detections
* Missing Fastener detections
* Vibration-event status
* Unified inspection status

---

## Pipeline

The complete processing pipeline consists of the following stages.

### 1. Camera Data Extraction

`00_extract_camera_data.py`

Reads the ROS2 bag and extracts the camera-side data required by the inspection pipeline.

Extracted data includes:

* RGB camera frames
* RGB frame timestamps
* IMU data
* Depth frames
* Depth timestamps
* Camera calibration parameters

Main outputs:

* `extracted/rgb/`
* `img_times.npy`
* `imu_raw.npy`
* `depth/`
* `depth_times.npy`
* `cam_K.npy`
* `cam_D.npy`

---

### 2. Track Vibration and Odometry Extraction

`01_extract_track_data.py`

Reads the ROS2 bag and extracts:

* Robot odometry timestamps
* Robot odometry track positions
* Track vibration timestamps
* Track vibration velocity measurements

Main outputs:

* `odom_time.npy`
* `odom_x.npy`
* `vib_time.npy`
* `vib_value.npy`

---

### 3. Spatial Position Estimation

`02_build_positions.py`

Uses odometry interpolation to estimate the track position corresponding to each camera frame and each vibration measurement.

The process is:

```text
Image timestamp
      ↓
Odometry interpolation
      ↓
Camera track position
```

and:

```text
Vibration timestamp
      ↓
Odometry interpolation
      ↓
Vibration track position
```

Main outputs:

* `img_pos.npy`
* `vib_pos.npy`

---

### 4. Camera–Vibration Spatial Synchronization

`03_build_mapping.py`

The camera and vibration measurement point are spatially separated. A calibrated constant camera-to-sensor offset of 1.3 m is used to establish spatial correspondence.

For each camera frame:

```text
Camera track position
        ↓
+ 1.3 m spatial offset
        ↓
Target vibration position
        ↓
Find nearest vibration position
        ↓
Assign corresponding vibration value
```

The vibration sample with the minimum absolute spatial difference from the target position is assigned to the corresponding camera frame.

Main outputs:

* `frame_vibration_final.npy`
* `frame_status.npy`

This produces a frame-level vibration sequence synchronized with the RGB video.

---

### 5. Vibration Event Identification

`04_detect_events.py`

The synchronized frame-level vibration sequence is analyzed to identify unusually high vibration responses.

The procedure is:

1. Only valid vibration measurements are considered.
2. The 99th percentile of the valid vibration values is calculated as the event threshold.
3. Frames exceeding this threshold are selected as candidate event frames.
4. Candidate frames separated by no more than 5 frames are grouped into the same event.
5. The frame with the maximum vibration value in each group is selected as the representative event frame.

Main output:

* `event_frames.npy`

These representative event frames are used by the final dashboard for vibration-event indication.

---

### 6. YOLO Detection and Dashboard Generation

`05_dashboard_yolo.py`

The final stage combines the synchronized vibration information with YOLO-based visual inspection.

The trained YOLO model detects four classes:

```text
0 - Fastener
1 - Sleeper
2 - Railway Track
3 - Missing Fastener
```

#### Final YOLO Configuration

| Parameter | Value |
|---|---:|
| IoU threshold | 0.30 |
| Fastener confidence | 0.05 |
| Sleeper confidence | 0.40 |
| Railway Track confidence | 0.10 |
| Missing Fastener confidence | 0.08 |

Class-specific confidence thresholds are applied after YOLO inference.

For visualization:

* Bounding boxes and labels are retained for all four classes.
* Fastener masks are displayed.
* Missing Fastener masks are displayed.
* Sleeper masks are suppressed.
* Railway Track masks are suppressed.

The dashboard combines visual detections and vibration-event information to determine the inspection status for each frame:

```text
NORMAL
VIBRATION EVENT
MISSING FASTENER
VIBRATION + MISSING FASTENER
ROLLER NOT REACHED
```

The final dashboard is generated in a 1280 × 720 landscape format.

Main output:

* `final_dashboard_yolo_v2.mp4`

---

## Repository Structure

```text
pipeline/
├── 00_extract_camera_data.py
├── 01_extract_track_data.py
├── 02_build_positions.py
├── 03_build_mapping.py
├── 04_detect_events.py
└── 05_dashboard_yolo.py

README.md
```
--

## Processing Flow

```text
                         ROS2 Bag
                            │
              ┌─────────────┴─────────────┐
              │                           │
       Camera / RGB Data            Track Data
              │                           │
              └─────────────┬─────────────┘
                            ↓
                    Data Extraction
                            ↓
                 Spatial Position Estimation
                            ↓
            Camera–Vibration Spatial Synchronization
                            ↓
              Frame-Level Vibration Sequence
                            │
                            ├──────────────→ Vibration Event Identification
                            │
                            ↓
                 YOLO Component Detection
                            │
                            ↓
                 Missing Fastener Detection
                            │
                            ↓
                 Unified Inspection Status
                            ↓
                1280 × 720 Dashboard
```

---

## Main Outputs

The main intermediate and final outputs are:

```text
img_pos.npy
vib_pos.npy
frame_vibration_final.npy
frame_status.npy
event_frames.npy
final_dashboard_yolo_v2.mp4
```

The NumPy files contain spatial positions, synchronized vibration measurements, vibration-data validity information, and representative vibration-event frames.

---

## Technologies Used

* Python
* ROS2
* NumPy
* OpenCV
* Ultralytics YOLO
* rosbags

---

## Results

The final system provides:

* Spatial synchronization of RGB frames and vibration measurements
* Camera-to-sensor spatial offset compensation
* Frame-level vibration values associated with camera frames
* Identification and spatial localization of high-vibration events
* Four-class railway component and defect detection using YOLO
* Missing Fastener detection
* Unified visual and vibration-based inspection status
* A 1280 × 720 landscape railway inspection dashboard

---

## Reproducibility

The pipeline should be executed sequentially:

```text
00_extract_camera_data.py
        ↓
01_extract_track_data.py
        ↓
02_build_positions.py
        ↓
03_build_mapping.py
        ↓
04_detect_events.py
        ↓
05_dashboard_yolo.py
```

The ROS2 bag and trained four-class YOLO model are required to reproduce the complete pipeline.

The trained model used by the dashboard is:

```text
best_v3_4class_981images.pt
```

The intermediate NumPy files generated by each stage are passed to the subsequent processing stages.

---

## Notes

* The final camera-to-sensor spatial offset is 1.3 m.
* Vibration events are identified using the 99th percentile of the valid synchronized vibration sequence.
* Candidate vibration-event frames are grouped using a maximum separation of 5 frames.
* The final dashboard uses an IoU threshold of 0.30 and class-specific confidence thresholds.
* The earlier scrolling vibration plot is not part of the final dashboard.
