import cv2
import numpy as np
from sort.sort import Sort
from ultralytics import YOLO
from util import get_car, license_complies_format, read_license_plate
import csv
import psutil
import os

# Initialize the tracker
results = {}
mot_tracker = Sort()

# Load models
coco_model = YOLO('yolov8n.pt')
license_plate_detector = YOLO('C:/Users/Jesser/Desktop/oo/models/license_plate_detector.pt')

# Load video from camera (change 0 to the appropriate camera index if you have multiple)
cap = cv2.VideoCapture(1)

vehicles = [2, 3, 5, 7]

# Get the process ID and create a process object
pid = os.getpid()
process = psutil.Process(pid)

# Read frames
frame_nmr = -1
while True:
    frame_nmr += 1
    ret, frame = cap.read()
    if not ret:
        break

    # Detect vehicles using YOLOv8
    detections = coco_model(frame, verbose=False)[0]
    detections_ = []
    for detection in detections.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = detection
        if int(class_id) in vehicles:
            detections_.append([x1, y1, x2, y2, score])

    # Track vehicles using SORT
    if detections_:
        track_ids = mot_tracker.update(np.asarray(detections_))
    else:
        track_ids = []

    # Detect license plates using license plate detector
    license_plates = license_plate_detector(frame, verbose=False)[0]
    for license_plate in license_plates.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = license_plate

        # Assign license plate to car using SORT tracking IDs
        xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)

        if car_id != -1:
            # Crop license plate
            license_plate_crop = frame[int(y1):int(y2), int(x1): int(x2), :]

            # Process license plate
            license_plate_crop_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
            _, license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray, 64, 255, cv2.THRESH_BINARY_INV)
            cv2.imshow('License Plate Thresholded', cv2.resize(license_plate_crop_thresh, (400, 100)))
            cv2.moveWindow('License Plate Thresholded', 50, 50)

            # Read license plate number using EasyOCR or other methods
            license_plate_text, license_plate_text_score = read_license_plate(license_plate_crop_thresh)

            # Display license plate text on the frame
            if license_plate_text is not None:
                if license_complies_format(license_plate_text):  # Assuming this checks the format
                    print(license_plate_text)

                # Store license plate information
                if frame_nmr not in results:
                    results[frame_nmr] = {}
                results[frame_nmr][car_id] = {
                    'car': {'bbox': [xcar1, ycar1, xcar2, ycar2]},
                    'license_plate': {
                        'bbox': [x1, y1, x2, y2],
                        'text': license_plate_text,
                        'bbox_score': score,
                        'text_score': license_plate_text_score
                    }
                }

        # Draw bounding boxes and text on the frame (uncomment if needed)
        cv2.rectangle(frame, (int(xcar1), int(ycar1)), (int(xcar2), int(ycar2)), (0, 255, 0), 2)
        cv2.putText(frame, f'Car {car_id}', (int(xcar1), int(ycar1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)

    # Display the frame
    cv2.imshow('Video', frame)

    # Exit on 'q' press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Save results to a CSV file
with open('license_plate_results.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Frame Number', 'Car ID', 'Car BBox', 'License Plate BBox', 'License Plate Text', 'BBox Score', 'Text Score'])

    for frame_nmr, cars in results.items():
        for car_id, data in cars.items():
            license_plate = data['license_plate']
            if license_plate['bbox_score'] > 0.8:  # Example threshold for good score
                writer.writerow([
                    frame_nmr,
                    car_id,
                    data['car']['bbox'],
                    license_plate['bbox'],
                    license_plate['text'],
                    license_plate['bbox_score'],
                    license_plate['text_score']
                ])
