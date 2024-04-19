import cvzone
import cv2
from datetime import datetime
import math
import requests
from sort import *
import time
from ultralytics import YOLO


traffic_analytics_service_url = "http://localhost:8000/add_traffic_record"
traffic_regulation_service_url = "http://localhost:7000/add_traffic_record"

# webcam source
# cap = cv2.VideoCapture(0)
# cap.set(3, 640)
# cap.set(4, 480)

# video source
cap = cv2.VideoCapture("resources/intersection.mp4")

model = YOLO("yolo-weights/yolov8n.pt")

# object classes
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

# detection mask
mask = cv2.imread("resources/mask.png")

# vehicle tracker
tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3)

# road sections
section1 = {"x_min": 0, "y_min": 0, "x_max": 540, "y_max": 370}  # road 1 coordinates
section2 = {"x_min": 560, "y_min": 200, "x_max": 1200, "y_max": 430}  # road 2 coordinates
section3 = {"x_min": 400, "y_min": 450, "x_max": 1150, "y_max": 710}  # road 3 coordinates

start_time = time.time()

interval = 20  # information every 10 seconds

while True:
    success, img = cap.read()

    img_region = cv2.bitwise_and(img, mask)

    results = model(img_region, stream=True)

    detections = np.empty((0, 5))

    # draw lines to visualize the road sections
    cv2.rectangle(img, (section1["x_min"], section1["y_min"]), (section1["x_max"], section1["y_max"]), (0, 255, 0),
                  2)  # road 1 green rectangle
    cv2.rectangle(img, (section2["x_min"], section2["y_min"]), (section2["x_max"], section2["y_max"]), (0, 0, 255),
                  2)  # road 2 red rectangle
    cv2.rectangle(img, (section3["x_min"], section3["y_min"]), (section3["x_max"], section3["y_max"]), (255, 0, 0),
                  2)  # road 3 blue rectangle

    for r in results:
        boxes = r.boxes
        for box in boxes:
            # bounding box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            # cv2.rectangle(img, (x1, y1), (x2, y2), (255, 165, 0), 3)
            w, h = x2 - x1, y2 - y1
            bbox = int(x1), int(y1), int(w), int(h)
            # cvzone.cornerRect(img, bbox, l=15, rt=1, t=1, colorR=(255, 165, 0), colorC=(255, 165, 0))

            # confidence
            conf = math.ceil((box.conf[0] * 100)) / 100

            # class name
            cls = int(box.cls[0])
            current_class = class_names[cls]
            if (current_class == "car" or current_class == "truck" or current_class == "bus" or
                    current_class == "motorbike" and conf > 0.1):
                # cvzone.cornerRect(img, bbox, l=15, rt=1, t=1, colorR=(255, 165, 0), colorC=(255, 165, 0))
                # cvzone.putTextRect(img, f'{current_class} {conf}', (max(0, x1), max(30, y1)), scale=0.7,
                #                    thickness=1, colorR=(255, 165, 0), offset=3)
                current_array = np.array([x1, y1, x2, y2, conf])
                detections = np.vstack((detections, current_array))

    results_tracker = tracker.update(detections)
    for result in results_tracker:
        x1, y1, x2, y2, car_id = result
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        w, h = x2 - x1, y2 - y1
        bbox = int(x1), int(y1), int(w), int(h)

        cvzone.cornerRect(img, bbox, l=15, rt=1, t=3, colorR=(255, 102, 102), colorC=(255, 102, 102))
        cvzone.putTextRect(img, f'Id: {int(car_id)}', (max(0, x1), max(30, y1)), scale=0.7,
                           thickness=1, colorR=(255, 102, 102), offset=3)

        cx, cy = x1 + w // 2, y1 + h // 2
        cv2.circle(img, (cx, cy), 5, (0, 128, 255), cv2.FILLED)

        # check which road section the car is in
        if section1["x_min"] <= x1 <= section1["x_max"] and section1["y_min"] <= y1 <= section1["y_max"]:
            road_name = "on road 1"
        elif section2["x_min"] <= x1 <= section2["x_max"] and section2["y_min"] <= y1 <= section2["y_max"]:
            road_name = "on road 2"
        elif section3["x_min"] <= x1 <= section3["x_max"] and section3["y_min"] <= y1 <= section3["y_max"]:
            road_name = "on road 3"
        else:
            road_name = "outside the roads"

        # print(f"Vehicle nr.{int(car_id)} is {road_name}")
        # print(f"Coordinates: {x1}, {x2}, {y1}, {y2}")

    cv2.imshow("Camera", img)

    # check if it's time to print traffic information
    elapsed_time = time.time() - start_time
    print(elapsed_time)
    if elapsed_time >= interval:
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        traffic_data = [{
            "time": current_time,
            "vehicle_count": (len([car for car in results_tracker if
                                   section1['x_min'] <= car[0] <= section1['x_max'] and
                                   section1['y_min'] <= car[1] <= section1['y_max']]) +
                              len([car for car in results_tracker if
                                   section3['x_min'] <= car[0] <= section3['x_max'] and
                                   section3['y_min'] <= car[1] <= section3['y_max']])),
            "pedestrian_count": len([car for car in results_tracker if
                                     section2['x_min'] <= car[0] <= section2['x_max'] and
                                     section2['y_min'] <= car[1] <= section2['y_max']]),
            "traffic_light_id": 1
        }]

        print("Sending new traffic data...", traffic_data)

        try:
            response = requests.post(traffic_analytics_service_url, json=traffic_data)

            if response.status_code == 200:
                print("Data successfully sent to Traffic Analytics Server")
            else:
                print("Failed to send data to Traffic Analytics Server. Status code:", response.status_code)

        except requests.exceptions.RequestException as e:
            print("Error occurred while sending data to Traffic Analytics Server:", e)

        try:
            response = requests.post(traffic_regulation_service_url, json=traffic_data)

            if response.status_code == 200:
                print("Data successfully sent to the Traffic Regulation Server")
            else:
                print("Failed to send data to Traffic Regulation Server. Status code:", response.status_code)

        except requests.exceptions.RequestException as e:
            print("Error occurred while sending data to Traffic Regulation Server:", e)

        start_time = time.time()

    key = cv2.waitKey(1)
    if key == 27:  # press 'Esc' to exit the loop
        break

cv2.destroyAllWindows()
cap.release()
