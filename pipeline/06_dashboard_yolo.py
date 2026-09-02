import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO


# ============================================================
# CONFIG
# ============================================================

FPS = 30

MODEL_PATH = "./model/best_v3_4class_981images.pt"

RGB_DIR = Path("./extracted/rgb")

IMG_POS_PATH = "./extracted/img_pos.npy"
VIB_PATH = "./extracted/frame_vibration_final.npy"
EVENT_PATH = "./extracted/event_frames.npy"

OUTPUT = "final_dashboard_yolo_v2.mp4"

# YOLO
CONF = 0.05
IOU = 0.30
DEVICE = 0

# Class IDs:
# 0 = Fastener
# 1 = Sleeper
# 2 = Railway Track
# 3 = Missing Fastener

CLASS_CONF = {
    0: 0.05,
    1: 0.40,
    2: 0.10,
    3: 0.08
}

# Final video
OUTPUT_W = 1280
OUTPUT_H = 720

# Camera
CAMERA_H = 720

# Plot
PLOT_H = 280

# Minimap
MINIMAP_W = 320
MINIMAP_H = 120

# Scrolling plot
PLOT_WINDOW_HALF = 0.5




# ============================================================
# LOAD DATA
# ============================================================

print("Loading data...")

img_pos = np.load(IMG_POS_PATH)
vib = np.load(VIB_PATH)
events = np.load(EVENT_PATH)

total = len(img_pos)

print("Frames:", total)


# ============================================================
# LOAD YOLO
# ============================================================

print("Loading YOLO model...")

model = YOLO(MODEL_PATH)

print("YOLO classes:")
print(model.names)


# ============================================================
# VIBRATION RANGE
# ============================================================

valid_vib = vib[~np.isnan(vib)]

if len(valid_vib) > 0:
    vib_min = np.min(valid_vib)
    vib_max = np.max(valid_vib)
else:
    vib_min = 0
    vib_max = 1

track_min = np.min(img_pos)
track_max = np.max(img_pos)


# ============================================================
# EVENT WINDOW
# ============================================================

event_set = set()

for e in events:

    for k in range(-15, 16):

        idx = int(e) + k

        if 0 <= idx < total:
            event_set.add(idx)


# YOLO Missing Fastener event frames
yolo_event_frames = []


# ============================================================
# VIDEO WRITER
# ============================================================

writer = cv2.VideoWriter(
    OUTPUT,
    cv2.VideoWriter_fourcc(*"mp4v"),
    FPS,
    (OUTPUT_W, OUTPUT_H)
)

if not writer.isOpened():
    raise RuntimeError("Could not open video writer")


# ============================================================
# MAIN LOOP
# ============================================================

for i in range(total):

    if i % 100 == 0:

        print(
            f"Processing {i}/{total} "
            f"({100 * i / total:.1f}%)"
        )

    # ========================================================
    # LOAD IMAGE
    # ========================================================

    frame_path = RGB_DIR / f"{i:05d}.png"

    frame = cv2.imread(str(frame_path))

    if frame is None:

        print("Could not read:", frame_path)

        continue


    # ========================================================
    # YOLO INFERENCE
    # ========================================================

    results = model.predict(
        source=frame,
        conf=CONF,
        iou=IOU,
        device=DEVICE,
        verbose=False
    )

    result = results[0]


    # ========================================================
    # CLASS-SPECIFIC CONFIDENCE FILTER
    # ========================================================

    if result.boxes is not None and len(result.boxes) > 0:

        keep = []

        for j in range(len(result.boxes)):

            cls = int(result.boxes.cls[j])
            score = float(result.boxes.conf[j])

            threshold = CLASS_CONF.get(cls, CONF)

            if score >= threshold:
                keep.append(j)


        if len(keep) > 0:

            keep = np.array(
                keep,
                dtype=np.int64
            )

            result.boxes = result.boxes[keep]

            if result.masks is not None:
                result.masks = result.masks[keep]

        else:

            result.boxes = result.boxes[:0]

            if result.masks is not None:
                result.masks = result.masks[:0]

    # ========================================================
    # MISSING FASTENER DETECTION
    # ========================================================

    missing_fastener_detected = False

    if result.boxes is not None and len(result.boxes) > 0:

        class_ids = result.boxes.cls.cpu().numpy().astype(int)

        if 3 in class_ids:
            missing_fastener_detected = True
            yolo_event_frames.append(i)           


    # ========================================================
    # DRAW YOLO OUTPUT
    # Sleeper and Railway Track masks are hidden.
    # Fastener and Missing Fastener masks are retained.
    # ========================================================

    annotated = result.plot(
        masks=False,
        boxes=True,
        labels=True
    )

    # Draw masks only for Fastener (0) and Missing Fastener (3)
    if result.masks is not None and result.boxes is not None:

        mask_data = result.masks.data.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy().astype(int)

        for mask, cls in zip(mask_data, class_ids):

            if cls not in [0, 3]:
                continue

            mask = cv2.resize(
                mask.astype(np.uint8),
                (frame.shape[1], frame.shape[0]),
                interpolation=cv2.INTER_NEAREST
            )

            mask_bool = mask > 0

            overlay = annotated.copy()

            if cls == 0:
                overlay[mask_bool] = (255, 0, 0)
            elif cls == 3:
                overlay[mask_bool] = (0, 0, 255)

            annotated = cv2.addWeighted(
                overlay,
                0.35,
                annotated,
                0.65,
                0
            )

        # ========================================================
    # LANDSCAPE CAMERA IMAGE
    # ========================================================

    # Reserve bottom 80 pixels for the information strip
    CAMERA_H = OUTPUT_H - 80

    annotated = cv2.resize(
        annotated,
        (OUTPUT_W, CAMERA_H)
    )

    # ========================================================
    # CAMERA CANVAS
    # ========================================================

    camera_canvas = np.ones(
        (CAMERA_H, OUTPUT_W, 3),
        dtype=np.uint8
    ) * 255

    # Center the landscape camera image
    x_offset = (OUTPUT_W - annotated.shape[1]) // 2

    camera_canvas[
        :,
        x_offset:x_offset + annotated.shape[1]
    ] = annotated



    # ========================================================
    # TRACK POSITION / VIBRATION
    # ========================================================

    position = float(img_pos[i])
    vibration = vib[i]


    # ========================================================
    # INFO STRIP
    # ========================================================

    info = np.ones(
        (80, 1280, 3),
        dtype=np.uint8
    ) * 255


    if np.isnan(vibration):

        vib_text = "NO DATA"
        status = "ROLLER NOT REACHED"

    else:

        vib_text = f"{vibration:.3f}"

        vibration_event = i in event_set

        if vibration_event and missing_fastener_detected:
            status = "VIBRATION + MISSING FASTENER"

        elif missing_fastener_detected:
            status = "MISSING FASTENER"

        elif vibration_event:
            status = "VIBRATION EVENT"

        else:
            status = "NORMAL"


    # Track position

    cv2.putText(
        info,
        f"Track Position: {position:.3f} m",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 0),
        2
    )


    # Vibration

    cv2.putText(
        info,
        f"Vibration: {vib_text}",
        (470, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 0),
        2
    )


    if status == "NORMAL":
        status_color = (0, 0, 0)

    elif status == "ROLLER NOT REACHED":
        status_color = (0, 0, 0)

    else:
        status_color = (0, 0, 255)


    cv2.putText(
        info,
        f"Status: {status}",
        (850, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        status_color,
        2
    )


    # ========================================================
    # MINIMAP
    # ========================================================

    minimap = np.ones(
        (MINIMAP_H, MINIMAP_W, 3),
        dtype=np.uint8
    ) * 255

    valid_idx = np.where(~np.isnan(vib))[0]

    if len(valid_idx) > 1:

        pts = []

        for idx in valid_idx:

            x = (
                (img_pos[idx] - track_min)
                / (track_max - track_min + 1e-9)
            ) * (MINIMAP_W - 1)

            y = (
                1.0
                - (vib[idx] - vib_min)
                / (vib_max - vib_min + 1e-9)
            ) * (MINIMAP_H - 20)

            pts.append([
                int(x),
                int(y) + 10
            ])


        pts = np.array(
            pts,
            dtype=np.int32
        )


        cv2.polylines(
            minimap,
            [pts],
            False,
            (255, 0, 0),
            1
        )


    curr_x = int(
        (
            (position - track_min)
            / (track_max - track_min + 1e-9)
        ) * (MINIMAP_W - 1)
    )

    curr_x = max(
        0,
        min(MINIMAP_W - 1, curr_x)
    )


    cv2.line(
        minimap,
        (curr_x, 0),
        (curr_x, MINIMAP_H),
        (0, 0, 255),
        2
    )


    cv2.rectangle(
        minimap,
        (0, 0),
        (MINIMAP_W - 1, MINIMAP_H - 1),
        (0, 0, 0),
        1
    )


    cv2.putText(
        minimap,
        "Full Track",
        (10, 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 0),
        1
    )


    camera_canvas[
        20:20 + MINIMAP_H,
        940:940 + MINIMAP_W
    ] = minimap

    # ========================================================
    # COMBINE
    # ========================================================

    dashboard = np.vstack([
        camera_canvas,
        info
    ])


    # ========================================================
    # SAFETY CHECK
    # ========================================================

    if dashboard.shape != (720, 1280, 3):

        print(
            "Unexpected dashboard shape:",
            dashboard.shape
        )

        continue


    writer.write(dashboard)


# ============================================================
# FINISH
# ============================================================

writer.release()

# ============================================================
# SAVE YOLO MISSING-FASTENER EVENT FRAMES
# ============================================================

yolo_event_frames = np.array(
    yolo_event_frames,
    dtype=int
)

np.save(
    "../extracted/yolo_event_frames.npy",
    yolo_event_frames
)

print(
    "Saved YOLO Missing Fastener event frames:",
    len(yolo_event_frames)
)

print()
print("======================================")
print("DONE")
print("Saved:", OUTPUT)
print("Global YOLO threshold:", CONF)
print("Fastener threshold:", CLASS_CONF[0])
print("Sleeper threshold:", CLASS_CONF[1])
print("Railway Track threshold:", CLASS_CONF[2])
print("Missing Fastener threshold:", CLASS_CONF[3])
print("YOLO IoU:", IOU)
print("======================================")
