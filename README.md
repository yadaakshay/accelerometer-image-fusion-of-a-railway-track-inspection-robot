# Track Vibration Fusion

## Overview

This project synchronizes RGB camera imagery with track vibration measurements using robot odometry. The goal is to identify potential track anomalies by associating each camera frame with the vibration measured at the corresponding track location.

The pipeline processes data recorded in a ROS2 bag and produces a dashboard video showing:

* RGB camera view
* Track position
* Vibration value
* Detected anomaly status
* Track vibration profile with a moving position indicator

---

## Pipeline

### 1. Data Extraction

Extract RGB images, image timestamps, odometry data, and track vibration velocity from the ROS2 bag.

Outputs:

* RGB images
* Image timestamps
* Odometry timestamps and positions
* Vibration timestamps and values

### 2. Position Estimation

Using odometry interpolation:

* Image timestamps → Track positions
* Vibration timestamps → Track positions

Outputs:

* `img_pos.npy`
* `vib_pos.npy`

### 3. Camera–Roller Offset Compensation

The camera is mounted approximately 1.2 m ahead of the vibration measurement roller.

For each image frame:

Track Position (Camera) → Corresponding Track Position (Roller)

Outputs:

* `frame_vibration_final.npy`
* `frame_status.npy`

### 4. Event Detection

High-vibration regions are detected using a percentile-based threshold and grouped into individual events.

Outputs:

* `event_frames.npy`

### 5. Visualization

A dashboard video is generated showing:

* RGB frame
* Track position
* Vibration measurement
* Event status
* Full vibration profile with current viewing region highlighted

Output:

* `dashboard_video.mp4`

---

## Repository Structure

```text
pipeline/
├── 00_extract_camera_data.py
├── 01_extract_track_data.py
├── 03_build_positions.py
├── 04_build_mapping.py
├── 05_detect_events.py
├── 05_generate_plot_background.py
└── 06_dashboard_video.py

validation/
├── 02_check_timestamps.py
└── check_mapping.py
```

---

## Technologies Used

* Python
* ROS2
* NumPy
* OpenCV
* Matplotlib
* rosbags

---

## Results

The system successfully:

* Synchronized camera frames with vibration measurements
* Compensated for sensor offset
* Detected high-vibration track regions
* Generated an inspection dashboard video for visual analysis

---
