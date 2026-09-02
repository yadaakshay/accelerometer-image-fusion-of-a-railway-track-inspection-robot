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

Vibration timestamp
      ↓
Odometry interpolation
      ↓
Vibration track position

---

### 3. Spatial Position Estimation
