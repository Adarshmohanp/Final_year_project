# backend/app.py - Modified version to avoid JAX conflict
import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'  # Add this at the very top

from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
import numpy as np
import cv2
from tensorflow.keras.preprocessing import image
from werkzeug.utils import secure_filename
import base64
import sys
from dotenv import load_dotenv
import requests
from google import genai


load_dotenv()
API_KEY = os.getenv('API_KEY')
client = genai.Client(api_key=API_KEY)
# Print Python path for debugging
print("Python executable:", sys.executable)
print("TensorFlow version:", tf.__version__)

app = Flask(__name__)
CORS(app)

# Configuration - adjust these paths based on your structure
MODEL_PATH = 'mri_model.keras'  # Go up one level from backend folder
# TRAIN_DIR = '../crop_train'        # Go up one level from backend folder
categories = ['glioma', 'meningioma', 'no_tumor','pituitary']  # Default categories if train dir is not found
UPLOAD_FOLDER = 'uploads'
RES = 240
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create upload folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load model and categories
print("Loading model...")
try:
    # Try to load with custom options to avoid conflicts
    model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("Please check the MODEL_PATH and ensure the model file exists")
    sys.exit(1)

# Get categories from training folder
try:
    print(f"📂 Using categories: {categories}")
except Exception as e:
    print(f"❌ Error loading categories: {e}")
    categories = ['glioma', 'meningioma', 'no_tumor', 'pituitary']  # Default fallback
    print(f"📂 Using default categories: {categories}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_heatmap(heatmap):
    """Analyze Grad-CAM heatmap to estimate tumor region"""

    heatmap_uint8 = np.uint8(255 * heatmap)

    # Detect strong activation areas
    _, thresh = cv2.threshold(heatmap_uint8, 150, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    tumor_area = 0

    for c in contours:
        tumor_area += cv2.contourArea(c)

    total_area = heatmap.shape[0] * heatmap.shape[1]

    coverage = (tumor_area / total_area) * 100

    return contours, tumor_area, coverage


# def get_tumor_location(contours, width, height):
#     """Estimate tumor location in the MRI"""

#     if len(contours) == 0:
#         return "No strong activation detected"

#     # largest = max(contours, key=cv2.contourArea)

#     # x, y, w, h = cv2.boundingRect(largest)



#     center_x = x + w/2
#     center_y = y + h/2

#     if center_x < width/2:
#         horizontal = "Left"
#     else:
#         horizontal = "Right"

#     if center_y < height/2:
#         vertical = "Upper"
#     else:
#         vertical = "Lower"

#     return f"{vertical}-{horizontal} region"

def get_tumor_location(contours, width, height):
    """Estimate tumor location in the MRI using top activation regions"""

    if len(contours) == 0:
        return "No strong activation detected"

    # Sort contours by area (largest first)
    sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)

    regions = []

    # Analyze top 2 activation regions
    for c in sorted_contours[:2]:

        x, y, w, h = cv2.boundingRect(c)

        center_x = x + w / 2
        center_y = y + h / 2

        # Horizontal location
        if center_x < width / 2:
            horizontal = "Left"
        else:
            horizontal = "Right"

        # Vertical location
        if center_y < height / 2:
            vertical = "Upper"
        else:
            vertical = "Lower"

        region = f"{vertical}-{horizontal}"

        # Avoid duplicates
        if region not in regions:
            regions.append(region)

    # Join multiple regions
    return ", ".join(regions) + " region"

def find_conv_layer(model):
    """Find the last convolutional layer in the model"""
    for layer in reversed(model.layers):
        if 'conv' in layer.name.lower() and 'project' in layer.name.lower():
            return layer.name
    # Fallback: try to find any conv layer
    for layer in reversed(model.layers):
        if 'conv' in layer.name.lower():
            return layer.name
    return None

# def generate_gradcam(img_path):
#     """Generate Grad-CAM heatmap for the image"""

#     img_check = image.load_img(img_path)
#     print("Original image size:", img_check.size)
    
#     # Load and preprocess image
#     img = image.load_img(img_path, target_size=(RES, RES))
#     x_orig = image.img_to_array(img)
#     x_input = np.expand_dims(x_orig, axis=0)
    
#     # Find the right convolutional layer
#     target_layer_name = find_conv_layer(model)
#     if not target_layer_name:
#         # If no conv layer found, return without heatmap
#         print("Warning: No convolutional layer found for Grad-CAM")
#         predictions = model.predict(x_input, verbose=0)
#         pred_idx = np.argmax(predictions[0])
#         confidence = float(predictions[0][pred_idx])
        
#         # Convert original to base64
#         _, buffer_original = cv2.imencode('.jpg', cv2.cvtColor(x_orig.astype('uint8'), cv2.COLOR_RGB2BGR))
#         original_b64 = base64.b64encode(buffer_original).decode('utf-8')
        
#         return {
#             'prediction': categories[pred_idx],
#             'confidence': confidence * 100,
#             'original_image': original_b64,
#             'heatmap_image': original_b64,

#             'tumor_area_pixels': 0,
#             'tumor_coverage_percent': 0,
#             'tumor_location': "Activation analysis unavailable",

#             'all_probabilities': {
#                 categories[i]: float(predictions[0][i] * 100)
#                 for i in range(len(categories))
#             }
#         }
    
#     try:
#         # Get target layer
#         target_layer = model.get_layer(target_layer_name)
        
#         # Create Grad model
#         grad_model = tf.keras.models.Model(
#             [model.inputs], 
#             [target_layer.output, model.output]
#         )
        
#         # Compute gradients
#         with tf.GradientTape() as tape:
#             conv_outputs, predictions = grad_model(x_input)
#             if isinstance(predictions, list):
#                 predictions = predictions[0]
            
#             pred_idx = np.argmax(predictions[0])
#             confidence = float(predictions[0][pred_idx])
#             loss = predictions[:, pred_idx]
        
#         grads = tape.gradient(loss, conv_outputs)
#         weights = tf.reduce_mean(grads, axis=(0, 1, 2))
        
#         # Generate heatmap
#         output = conv_outputs[0]
#         heatmap = output @ weights[..., tf.newaxis]
#         heatmap = tf.squeeze(heatmap)
#         heatmap = tf.maximum(heatmap, 0)
        
#         if tf.reduce_max(heatmap) != 0:
#             heatmap = heatmap / tf.reduce_max(heatmap)
#         heatmap = heatmap.numpy()
        
#         # Resize and colorize heatmap
#         heatmap_resized = cv2.resize(heatmap, (RES, RES))
#         # ---- Analyze heatmap for tumor region ----
#         contours, tumor_area, coverage = analyze_heatmap(heatmap_resized)

#         # Draw bounding box around largest activation
#         # if len(contours) > 0:
#         #     largest = max(contours, key=cv2.contourArea)

#         #     x, y, w, h = cv2.boundingRect(largest)

#         #     cv2.rectangle(
#         #         img_display,
#         #         (x, y),
#         #         (x + w, y + h),
#         #         (255, 0, 0),
#         #         2
#         #     )


#         location = get_tumor_location(
#             contours,
#             heatmap_resized.shape[1],
#             heatmap_resized.shape[0]
#         )

#         if categories[pred_idx] == "no_tumor":
#             location = "No significant tumor-like activation detected"

#         print("📊 Tumor coverage:", coverage)
#         print("📍 Tumor location:", location)
#         heatmap_uint8 = np.uint8(255 * heatmap_resized)
#         heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
#         heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
        
#         # Superimpose
#         img_display = x_orig.astype('uint8')
#         superimposed = cv2.addWeighted(img_display, 0.6, heatmap_color, 0.4, 0)
        
#         # Convert to base64
#         _, buffer_original = cv2.imencode('.jpg', cv2.cvtColor(img_display, cv2.COLOR_RGB2BGR))
#         _, buffer_heatmap = cv2.imencode('.jpg', cv2.cvtColor(superimposed, cv2.COLOR_RGB2BGR))
        
#         original_b64 = base64.b64encode(buffer_original).decode('utf-8')
#         heatmap_b64 = base64.b64encode(buffer_heatmap).decode('utf-8')
        
#         # Get all probabilities
#         all_probs = predictions[0].numpy()
        
#         return {
#             'prediction': categories[pred_idx],
#             'confidence': confidence * 100,
#             'original_image': original_b64,
#             'heatmap_image': heatmap_b64,

#             'tumor_area_pixels': float(tumor_area),
#             'tumor_coverage_percent': float(coverage),
#             'tumor_location': location,

#             'all_probabilities': {
#                 categories[i]: float(all_probs[i] * 100) 
#                 for i in range(len(categories))
#             }
#         }
        
#     except Exception as e:
#         print(f"Grad-CAM generation failed: {e}")
#         # Fallback to simple prediction
#         predictions = model.predict(x_input, verbose=0)
#         pred_idx = np.argmax(predictions[0])
#         confidence = float(predictions[0][pred_idx])
        
#         _, buffer_original = cv2.imencode('.jpg', cv2.cvtColor(x_orig.astype('uint8'), cv2.COLOR_RGB2BGR))
#         original_b64 = base64.b64encode(buffer_original).decode('utf-8')
        
#         return {
#             'prediction': categories[pred_idx],
#             'confidence': confidence * 100,
#             'original_image': original_b64,
#             'heatmap_image': original_b64,

#             'tumor_area_pixels': 0,
#             'tumor_coverage_percent': 0,
#             'tumor_location': "Activation analysis unavailable",

#             'all_probabilities': {
#                 categories[i]: float(predictions[0][i] * 100)
#                 for i in range(len(categories))
#             }
#         }










# def generate_gradcam(img_path):
#     """Generate Grad-CAM heatmap and tumor location with colored overlay"""

#     # Load original image for display
#     img_orig = image.load_img(img_path, target_size=(RES, RES))
#     x_orig = image.img_to_array(img_orig)
#     x_input = np.expand_dims(x_orig, axis=0)

#     # Find last convolutional layer
#     target_layer_name = find_conv_layer(model)

#     if not target_layer_name:
#         # No conv layer, simple prediction fallback
#         predictions = model.predict(x_input, verbose=0)
#         pred_idx = np.argmax(predictions[0])
#         confidence = float(predictions[0][pred_idx])

#         _, buffer_original = cv2.imencode('.jpg', cv2.cvtColor(x_orig.astype('uint8'), cv2.COLOR_RGB2BGR))
#         original_b64 = base64.b64encode(buffer_original).decode('utf-8')

#         return {
#             'prediction': categories[pred_idx],
#             'confidence': confidence * 100,
#             'original_image': original_b64,
#             'heatmap_image': original_b64,
#             'tumor_area_pixels': 0,
#             'tumor_coverage_percent': 0,
#             'tumor_location': "Activation analysis unavailable",
#             'all_probabilities': {categories[i]: float(predictions[0][i] * 100) for i in range(len(categories))}
#         }

#     try:
#         # Grad-CAM setup
#         target_layer = model.get_layer(target_layer_name)
#         grad_model = tf.keras.models.Model([model.inputs], [target_layer.output, model.output])

#         with tf.GradientTape() as tape:
#             conv_outputs, predictions = grad_model(x_input)
#             if isinstance(predictions, list):
#                 predictions = predictions[0]

#             pred_idx = np.argmax(predictions[0])
#             confidence = float(predictions[0][pred_idx])
#             loss = predictions[:, pred_idx]

#         grads = tape.gradient(loss, conv_outputs)
#         weights = tf.reduce_mean(grads, axis=(0, 1, 2))

#         # Generate heatmap
#         output = conv_outputs[0]
#         heatmap = output @ weights[..., tf.newaxis]
#         heatmap = tf.squeeze(heatmap)
#         heatmap = tf.maximum(heatmap, 0)
#         if tf.reduce_max(heatmap) != 0:
#             heatmap = heatmap / tf.reduce_max(heatmap)
#         heatmap = heatmap.numpy()

#         # Resize heatmap to image size
#         heatmap_resized = cv2.resize(heatmap, (RES, RES))

#         # Analyze heatmap for tumor region
#         contours, tumor_area, coverage = analyze_heatmap(heatmap_resized)
#         location = get_tumor_location(contours, heatmap_resized.shape[1], heatmap_resized.shape[0])
#         if categories[pred_idx] == "no_tumor":
#             location = "No significant tumor-like activation detected"

#         # Prepare images
#         img_display = x_orig.astype('uint8')  # Original MRI for rectangle
#         heatmap_uint8 = np.uint8(255 * heatmap_resized)
#         heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
#         heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

#         # Draw blue rectangle on original MRI (largest contour)
#         if len(contours) > 0:
#             largest = max(contours, key=cv2.contourArea)
#             x, y, w, h = cv2.boundingRect(largest)
#             cv2.rectangle(
#                 img_display,
#                 (x, y),
#                 (x + w, y + h),
#                 (255, 0, 0),  # Blue in BGR
#                 2
#             )

#         # Superimpose heatmap over MRI (keep colors)
#         superimposed = cv2.addWeighted(img_display, 0.6, heatmap_color, 0.4, 0)

#         # Convert images to base64
#         _, buffer_original = cv2.imencode('.jpg', cv2.cvtColor(img_display, cv2.COLOR_RGB2BGR))
#         _, buffer_heatmap = cv2.imencode('.jpg', cv2.cvtColor(superimposed, cv2.COLOR_RGB2BGR))
#         original_b64 = base64.b64encode(buffer_original).decode('utf-8')
#         heatmap_b64 = base64.b64encode(buffer_heatmap).decode('utf-8')

#         # All probabilities
#         all_probs = predictions[0].numpy()

#         return {
#             'prediction': categories[pred_idx],
#             'confidence': confidence * 100,
#             'original_image': original_b64,
#             'heatmap_image': heatmap_b64,
#             'tumor_area_pixels': float(tumor_area),
#             'tumor_coverage_percent': float(coverage),
#             'tumor_location': location,
#             'all_probabilities': {categories[i]: float(all_probs[i] * 100) for i in range(len(categories))}
#         }

#     except Exception as e:
#         print(f"Grad-CAM generation failed: {e}")
#         # Fallback to simple prediction
#         predictions = model.predict(x_input, verbose=0)
#         pred_idx = np.argmax(predictions[0])
#         confidence = float(predictions[0][pred_idx])
#         _, buffer_original = cv2.imencode('.jpg', cv2.cvtColor(x_orig.astype('uint8'), cv2.COLOR_RGB2BGR))
#         original_b64 = base64.b64encode(buffer_original).decode('utf-8')

#         return {
#             'prediction': categories[pred_idx],
#             'confidence': confidence * 100,
#             'original_image': original_b64,
#             'heatmap_image': original_b64,
#             'tumor_area_pixels': 0,
#             'tumor_coverage_percent': 0,
#             'tumor_location': "Activation analysis unavailable",
#             'all_probabilities': {categories[i]: float(predictions[0][i] * 100) for i in range(len(categories))}
#         }





def generate_gradcam(img_path):
    """Generate Grad-CAM heatmap and tumor location with colored overlay"""

    # Load original image for display
    img_orig = image.load_img(img_path, target_size=(RES, RES))
    x_orig = image.img_to_array(img_orig)
    x_input = np.expand_dims(x_orig, axis=0)

    # Find last convolutional layer
    target_layer_name = find_conv_layer(model)

    if not target_layer_name:
        # No conv layer, simple prediction fallback
        predictions = model.predict(x_input, verbose=0)
        pred_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][pred_idx])

        _, buffer_original = cv2.imencode('.jpg', cv2.cvtColor(x_orig.astype('uint8'), cv2.COLOR_RGB2BGR))
        original_b64 = base64.b64encode(buffer_original).decode('utf-8')

        return {
            'prediction': categories[pred_idx],
            'confidence': confidence * 100,
            'original_image': original_b64,
            'heatmap_image': original_b64,
            'tumor_area_pixels': 0,
            'tumor_coverage_percent': 0,
            'tumor_location': "Activation analysis unavailable",
            'all_probabilities': {categories[i]: float(predictions[0][i] * 100) for i in range(len(categories))}
        }

    try:
        # Grad-CAM setup
        target_layer = model.get_layer(target_layer_name)
        grad_model = tf.keras.models.Model([model.inputs], [target_layer.output, model.output])

        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(x_input)
            if isinstance(predictions, list):
                predictions = predictions[0]

            pred_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][pred_idx])
            loss = predictions[:, pred_idx]

        grads = tape.gradient(loss, conv_outputs)
        weights = tf.reduce_mean(grads, axis=(0, 1, 2))

        # Generate heatmap
        output = conv_outputs[0]
        heatmap = output @ weights[..., tf.newaxis]
        heatmap = tf.squeeze(heatmap)
        heatmap = tf.maximum(heatmap, 0)
        if tf.reduce_max(heatmap) != 0:
            heatmap = heatmap / tf.reduce_max(heatmap)
        heatmap = heatmap.numpy()

        # Resize heatmap to image size
        heatmap_resized = cv2.resize(heatmap, (RES, RES))

        # Analyze heatmap for tumor region
        contours, tumor_area, coverage = analyze_heatmap(heatmap_resized)
        location = get_tumor_location(contours, heatmap_resized.shape[1], heatmap_resized.shape[0])
        if categories[pred_idx] == "no_tumor":
            location = "No significant tumor-like activation detected"

        # Prepare images
        # 1️⃣ Original MRI with blue box
        img_with_box = x_orig.astype('uint8')
        if categories[pred_idx] != "no_tumor" and len(contours) > 0:
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            cv2.rectangle(
                img_with_box,
                (x, y),
                (x + w, y + h),
                (255, 0, 0),  # Blue in BGR
                2
            )

        # 2️⃣ Heatmap overlay (Grad-CAM colors) without blue box
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
        superimposed = cv2.addWeighted(x_orig.astype('uint8'), 0.6, heatmap_color, 0.4, 0)

        # Convert both to base64
        _, buffer_original = cv2.imencode('.jpg', cv2.cvtColor(img_with_box, cv2.COLOR_RGB2BGR))
        _, buffer_heatmap = cv2.imencode('.jpg', cv2.cvtColor(superimposed, cv2.COLOR_RGB2BGR))
        original_b64 = base64.b64encode(buffer_original).decode('utf-8')
        heatmap_b64 = base64.b64encode(buffer_heatmap).decode('utf-8')

        # All probabilities
        all_probs = predictions[0].numpy()

        return {
            'prediction': categories[pred_idx],
            'confidence': confidence * 100,
            'original_image': original_b64,   # MRI with blue box
            'heatmap_image': heatmap_b64,     # Grad-CAM overlay only
            'tumor_area_pixels': float(tumor_area),
            'tumor_coverage_percent': float(coverage),
            'tumor_location': location,
            'all_probabilities': {categories[i]: float(all_probs[i] * 100) for i in range(len(categories))}
        }

    except Exception as e:
        print(f"Grad-CAM generation failed: {e}")
        # Fallback to simple prediction
        predictions = model.predict(x_input, verbose=0)
        pred_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][pred_idx])
        _, buffer_original = cv2.imencode('.jpg', cv2.cvtColor(x_orig.astype('uint8'), cv2.COLOR_RGB2BGR))
        original_b64 = base64.b64encode(buffer_original).decode('utf-8')

        return {
            'prediction': categories[pred_idx],
            'confidence': confidence * 100,
            'original_image': original_b64,
            'heatmap_image': original_b64,
            'tumor_area_pixels': 0,
            'tumor_coverage_percent': 0,
            'tumor_location': "Activation analysis unavailable",
            'all_probabilities': {categories[i]: float(predictions[0][i] * 100) for i in range(len(categories))}
        }



@app.route('/api/gemini-explain', methods=['POST'])
def gemini_explain():

    data = request.json

    prediction = data["prediction"]
    confidence = data["confidence"]
    location = data["tumor_location"]
    coverage = data["tumor_coverage"]

    prompt = f"""
                You are an AI assistant helping radiologists interpret MRI scans.

                MRI AI Model Output:
                Prediction: {prediction}
                Confidence: {confidence}%
                Estimated Tumor Coverage: {coverage}%
                Tumor Location: {location}

                Explain the result in a structured clinical format.

                Include:

                1. Short Interpretation
                2. Possible Clinical Meaning
                3. Typical Symptoms
                4. Recommended Next Steps

                Keep explanation concise and medically professional.
                """

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    return {
        "explanation": response.text
    }

def call_gemini_api(data):

    prediction = data["prediction"]
    confidence = data["confidence"]
    location = data["tumor_location"]
    coverage = data["tumor_coverage"]

    prompt = f"""
                You are an AI assistant helping radiologists interpret MRI scans.

                MRI AI Model Output:
                Prediction: {prediction}
                Confidence: {confidence}%
                Estimated Tumor Coverage: {coverage}%
                Tumor Location: {location}

                Explain the result in a structured clinical format.

                Include:

                1. Short Interpretation
                2. Possible Clinical Meaning
                3. Typical Symptoms
                4. Recommended Next Steps

                Keep explanation concise and medically professional.
                """

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    return {
        "explanation": response.text
    }


# def call_gemini_api(data):


# @app.route('/api/predict', methods=['POST'])
# def predict():
#     """Endpoint for MRI prediction"""
#     try:
#         if 'file' not in request.files:
#             return jsonify({'error': 'No file provided'}), 400
        
#         file = request.files['file']
        
#         if file.filename == '':
#             return jsonify({'error': 'No file selected'}), 400
        
#         if file and allowed_file(file.filename):
#             # Save temporarily
#             filename = secure_filename(file.filename)
#             temp_path = os.path.join(UPLOAD_FOLDER, filename)
#             file.save(temp_path)
            
#             # Generate prediction and heatmap
#             result = generate_gradcam(temp_path)
            
#             # Clean up temp file
#             os.remove(temp_path)
            
#             return jsonify({
#                 'success': True,
#                 'prediction': result['prediction'],
#                 'confidence': round(result['confidence'], 2),
#                 'original_image': result['original_image'],
#                 'heatmap_image': result['heatmap_image'],
#                 'all_probabilities': result['all_probabilities']
#             })
            
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return jsonify({'error': str(e)}), 500



@app.route('/api/predict', methods=['POST'])
def predict():
    """Endpoint for MRI prediction"""
    try:
        print("\n----- NEW MRI PREDICTION REQUEST -----")

        if 'file' not in request.files:
            print("❌ No file found in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        print("📁 Uploaded file name:", file.filename)

        if file.filename == '':
            print("❌ Empty filename")
            return jsonify({'error': 'No file selected'}), 400

        # Print extension
        ext = file.filename.split('.')[-1].lower()
        print("📄 File extension:", ext)

        if file and allowed_file(file.filename):

            # Save temporarily
            filename = secure_filename(file.filename)
            temp_path = os.path.join(UPLOAD_FOLDER, filename)

            print("💾 Saving file to:", temp_path)
            file.save(temp_path)

            # Check if file really exists
            if not os.path.exists(temp_path):
                print("❌ File was not saved correctly")
                return jsonify({'error': 'File saving failed'}), 500

            print("🧠 Running MRI prediction...")

            # Generate prediction
            result = generate_gradcam(temp_path)

            print("✅ Prediction complete")
            print("Predicted class:", result['prediction'])
            print("Confidence:", result['confidence'])

            # Clean up temp file
            os.remove(temp_path)
            print("🗑 Temporary file removed")

            return jsonify({
                # 'success': True,
                # 'prediction': result['prediction'],
                # 'confidence': round(result['confidence'], 2),
                # 'original_image': result['original_image'],
                # 'heatmap_image': result['heatmap_image'],
                # 'all_probabilities': result['all_probabilities']
                'success': True,
                'prediction': result['prediction'],
                'confidence': round(result['confidence'], 2),

                'tumor_location': result['tumor_location'],
                'tumor_coverage': round(result['tumor_coverage_percent'],2),

                'original_image': result['original_image'],
                'heatmap_image': result['heatmap_image'],
                'all_probabilities': result['all_probabilities']
            })

        else:
            print("❌ Unsupported file format")
            return jsonify({'error': 'Unsupported file format'}), 400
            
    except Exception as e:
        import traceback
        print("🔥 ERROR DURING PREDICTION")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    


@app.route('/api/test-image', methods=['POST'])
def test_image():
    """Simple endpoint that just returns prediction without heatmap"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            temp_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(temp_path)
            
            # Load and predict
            img = image.load_img(temp_path, target_size=(RES, RES))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            
            predictions = model.predict(img_array, verbose=0)
            pred_idx = np.argmax(predictions[0])
            confidence = predictions[0][pred_idx] * 100
            
            # Get top 3 predictions
            top_indices = np.argsort(predictions[0])[-3:][::-1]
            top_predictions = [
                {
                    'class': categories[i],
                    'confidence': round(float(predictions[0][i] * 100), 2)
                }
                for i in top_indices
            ]
            
            os.remove(temp_path)
            
            return jsonify({
                'success': True,
                'prediction': categories[pred_idx],
                'confidence': round(confidence, 2),
                'top_predictions': top_predictions
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'model_loaded': True,
        'categories': categories,
        'tensorflow_version': tf.__version__
    })

@app.route('/api/geminiexplain', methods=['POST'])
def geminiexplain():

    data = request.get_json()

    explanation = call_gemini_api(data)

    return jsonify(explanation)



if __name__ == '__main__':
    print("🚀 Starting Flask server...")
    print(f"📁 Model path: {MODEL_PATH}")
    print("🌐 Server will run on http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')