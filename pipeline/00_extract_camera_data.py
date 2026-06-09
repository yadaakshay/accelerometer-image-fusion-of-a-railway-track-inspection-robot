import numpy as np
import cv2
from pathlib import Path
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

BAG_PATH  = Path('/mnt/c/small_filtered_bag')
OUT_DIR   = Path('./extracted')
OUT_DIR.mkdir(exist_ok=True)
(OUT_DIR / 'rgb').mkdir(exist_ok=True)
(OUT_DIR / 'depth').mkdir(exist_ok=True)

typestore = get_typestore(Stores.ROS2_HUMBLE)

TOPICS = {
    '/left_tof/gyro_accel/sample',
    '/left_tof/color/image_raw/compressed',
    '/left_tof/depth/image_raw/compressedDepth',
    '/left_tof/color/camera_info',
}

imu_data    = []
img_times   = []
depth_times = []
cam_K       = None
cam_D       = None
img_idx     = 0
dep_idx     = 0

print("Extracting data from bag...")

with Reader(BAG_PATH) as reader:
    conns = [c for c in reader.connections if c.topic in TOPICS]
    for conn, ts, raw in reader.messages(connections=conns):
        msg = typestore.deserialize_cdr(raw, conn.msgtype)
        t = ts * 1e-9  # use bag timestamp

        if conn.topic == '/left_tof/gyro_accel/sample':
            imu_data.append([
                t,
                msg.linear_acceleration.x,
                msg.linear_acceleration.y,
                msg.linear_acceleration.z,
                msg.angular_velocity.x,
                msg.angular_velocity.y,
                msg.angular_velocity.z,
            ])

        elif conn.topic == '/left_tof/color/image_raw/compressed':
            arr = np.frombuffer(bytes(msg.data), np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is not None:
                cv2.imwrite(str(OUT_DIR / 'rgb' / f'{img_idx:05d}.png'), img)
                img_times.append(t)
                img_idx += 1
                if img_idx % 100 == 0:
                    print(f"  RGB frames: {img_idx}")

        elif conn.topic == '/left_tof/depth/image_raw/compressedDepth':
            raw_bytes = bytes(msg.data)
            arr = np.frombuffer(raw_bytes[12:], np.uint8)
            depth = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
            if depth is not None:
                np.save(str(OUT_DIR / 'depth' / f'{dep_idx:05d}.npy'), depth)
                depth_times.append(t)
                dep_idx += 1

        elif conn.topic == '/left_tof/color/camera_info' and cam_K is None:
            cam_K = np.array(msg.k).reshape(3, 3)
            cam_D = np.array(msg.d)
            print(f"\nCamera K:\n{cam_K}")
            print(f"Distortion D: {cam_D}\n")

# Save everything
np.save(OUT_DIR / 'imu_raw.npy',    np.array(imu_data))
np.save(OUT_DIR / 'img_times.npy',  np.array(img_times))
np.save(OUT_DIR / 'depth_times.npy',np.array(depth_times))
np.save(OUT_DIR / 'cam_K.npy',      cam_K)
np.save(OUT_DIR / 'cam_D.npy',      cam_D)

print(f"\nDone!")
print(f"  IMU samples  : {len(imu_data)}")
print(f"  RGB frames   : {img_idx}")
print(f"  Depth frames : {dep_idx}")
print(f"  Saved to     : {OUT_DIR}")
