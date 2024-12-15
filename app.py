from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
from ultralytics import YOLO
import base64
import traceback

app = Flask(__name__)

# Load the YOLO model
model = YOLO("yolov8n.pt")  # Make sure the correct model path is provided

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400
    
    image_file = request.files['image']
    
    # Check if the file is an image
    if not image_file.mimetype.startswith('image'):
        return jsonify({"error": "Uploaded file is not an image"}), 400

    try:
        # Read the image as a byte array
        image_bytes = image_file.read()
        image = np.asarray(bytearray(image_bytes), dtype=np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        # Check if image is read correctly
        if image is None:
            return jsonify({"error": "Failed to decode image"}), 400

        # Perform object detection using YOLOv8
        results = model(image)  # Perform detection

        # Get the annotated image (with bounding boxes)
        annotated_image = results[0].plot()  # Annotated image with bounding boxes

        # Convert the annotated image to base64 to send it to the frontend
        _, buffer = cv2.imencode('.jpg', annotated_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')  # Convert to base64 string

        # Prepare the detection information
        detections = []
        for box in results[0].boxes:
            # Extract box coordinates, class label, and confidence
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            label = results[0].names[int(box.cls)]  # Get class name from the box
            confidence = box.conf[0].cpu().numpy()  # Get confidence score

            detections.append({
                "x1": int(x1),
                "y1": int(y1),
                "x2": int(x2),
                "y2": int(y2),
                "label": label,
                "confidence": float(confidence)  # Ensure it's a float for JSON serialization
            })

        # Return the response with detections and the image in base64 format
        return jsonify({
            "detections": detections,
            "image": img_base64  # Send the image as base64
        })

    except Exception as e:
        # Log the exception with traceback
        error_message = f"Error occurred while processing the image: {str(e)}"
        traceback_message = traceback.format_exc()  # Get detailed traceback
        print(error_message)
        print(traceback_message)
        return jsonify({"error": "Error occurred while processing the image"}), 500

if __name__ == "__main__":
    app.run(debug=True)
