import cv2
from ultralytics import YOLO
import cvzone
import math
from sort import *

# webcam source
# cap = cv2.VideoCapture(0)
# cap.set(3, 640)
# cap.set(4, 480)

# video source
cap = cv2.VideoCapture("resources/intersection.mp4")

model = YOLO("yolo-weights/yolov8n.pt")

class_names = [
    "person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "sofa", "potted plant", "bed", "dining table", "toilet", "TV monitor", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator",
    "book", "clock", "vase", "scissors", "teddy bear", "hair dryer", "toothbrush"
]

mask = cv2.imread("resources/mask.png")

# tracking
tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3)

while True:
    success, img = cap.read()
    img_region = cv2.bitwise_and(img, mask)
    results = model(img_region, stream=True)
    detections = np.empty((0, 5))
    for r in results:
        boxes = r.boxes
        for box in boxes:
            # bounding box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            # cv2.rectangle(img, (x1, y1), (x2, y2), (255, 165, 0), 3)
            w, h = x2 - x1, y2 - y1
            bbox = int(x1), int(y1), int(w), int(h)
            # cvzone.cornerRect(img, bbox, l=15, rt=1, t=1, colorR=(235, 128, 52), colorC=(235, 128, 52))
            # confidence
            conf = math.ceil((box.conf[0] * 100)) / 100
            # class name
            cls = int(box.cls[0])
            current_class = class_names[cls]
            if (current_class == "car" or current_class == "truck" or current_class == "bus" or
                    current_class == "motorbike" and conf > 0.3):
                # cvzone.cornerRect(img, bbox, l=15, rt=1, t=1, colorR=(235, 128, 52), colorC=(235, 128, 52))
                # cvzone.putTextRect(img, f'{current_class} {conf}', (max(0, x1), max(30, y1)), scale=0.7,
                #                    thickness=1, colorR=(235, 128, 52), offset=3)
                current_array = np.array([x1, y1, x2, y2, conf])
                detections = np.vstack((detections, current_array))
    results_tracker = tracker.update(detections)
    for result in results_tracker:
        x1, y1, x2, y2, car_id = result
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        print(result)
        w, h = x2 - x1, y2 - y1
        bbox = int(x1), int(y1), int(w), int(h)
        cvzone.cornerRect(img, bbox, l=15, rt=1, t=3, colorR=(235, 128, 0), colorC=(235, 128, 0))
        cvzone.putTextRect(img, f'Id: {int(car_id)}', (max(0, x1), max(30, y1)), scale=0.7,
                           thickness=1, colorR=(235, 128, 52), offset=3)
        cx, cy = x1 + w // 2, y1 + h // 2
        cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
    cv2.imshow("Camera", img)
    cv2.waitKey(1)
