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

# Print Python path for debugging
print("Python executable:", sys.executable)
print("TensorFlow version:", tf.__version__)

app = Flask(__name__)
CORS(app)

# Configuration - adjust these paths based on your structure
MODEL_PATH = '../mri_model.keras'  # Go up one level from backend folder
TRAIN_DIR = '../crop_train'        # Go up one level from backend folder
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
    categories = sorted([d for d in os.listdir(TRAIN_DIR) 
                        if os.path.isdir(os.path.join(TRAIN_DIR, d))])
    print(f"📂 Categories found: {categories}")
except Exception as e:
    print(f"❌ Error loading categories: {e}")
    categories = ['glioma', 'meningioma', 'no_tumor', 'pituitary']  # Default fallback
    print(f"📂 Using default categories: {categories}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

def generate_gradcam(img_path):
    """Generate Grad-CAM heatmap for the image"""
    
    # Load and preprocess image
    img = image.load_img(img_path, target_size=(RES, RES))
    x_orig = image.img_to_array(img)
    x_input = np.expand_dims(x_orig, axis=0)
    
    # Find the right convolutional layer
    target_layer_name = find_conv_layer(model)
    if not target_layer_name:
        # If no conv layer found, return without heatmap
        print("Warning: No convolutional layer found for Grad-CAM")
        predictions = model.predict(x_input, verbose=0)
        pred_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][pred_idx])
        
        # Convert original to base64
        _, buffer_original = cv2.imencode('.jpg', cv2.cvtColor(x_orig.astype('uint8'), cv2.COLOR_RGB2BGR))
        original_b64 = base64.b64encode(buffer_original).decode('utf-8')
        
        return {
            'prediction': categories[pred_idx],
            'confidence': confidence * 100,
            'original_image': original_b64,
            'heatmap_image': original_b64,  # Just return original if no heatmap
            'all_probabilities': {
                categories[i]: float(predictions[0][i] * 100) 
                for i in range(len(categories))
            }
        }
    
    try:
        # Get target layer
        target_layer = model.get_layer(target_layer_name)
        
        # Create Grad model
        grad_model = tf.keras.models.Model(
            [model.inputs], 
            [target_layer.output, model.output]
        )
        
        # Compute gradients
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
        
        # Resize and colorize heatmap
        heatmap_resized = cv2.resize(heatmap, (RES, RES))
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
        
        # Superimpose
        img_display = x_orig.astype('uint8')
        superimposed = cv2.addWeighted(img_display, 0.6, heatmap_color, 0.4, 0)
        
        # Convert to base64
        _, buffer_original = cv2.imencode('.jpg', cv2.cvtColor(img_display, cv2.COLOR_RGB2BGR))
        _, buffer_heatmap = cv2.imencode('.jpg', cv2.cvtColor(superimposed, cv2.COLOR_RGB2BGR))
        
        original_b64 = base64.b64encode(buffer_original).decode('utf-8')
        heatmap_b64 = base64.b64encode(buffer_heatmap).decode('utf-8')
        
        # Get all probabilities
        all_probs = predictions[0].numpy()
        
        return {
            'prediction': categories[pred_idx],
            'confidence': confidence * 100,
            'original_image': original_b64,
            'heatmap_image': heatmap_b64,
            'all_probabilities': {
                categories[i]: float(all_probs[i] * 100) 
                for i in range(len(categories))
            }
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
            'all_probabilities': {
                categories[i]: float(predictions[0][i] * 100) 
                for i in range(len(categories))
            }
        }

@app.route('/api/predict', methods=['POST'])
def predict():
    """Endpoint for MRI prediction"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Save temporarily
            filename = secure_filename(file.filename)
            temp_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(temp_path)
            
            # Generate prediction and heatmap
            result = generate_gradcam(temp_path)
            
            # Clean up temp file
            os.remove(temp_path)
            
            return jsonify({
                'success': True,
                'prediction': result['prediction'],
                'confidence': round(result['confidence'], 2),
                'original_image': result['original_image'],
                'heatmap_image': result['heatmap_image'],
                'all_probabilities': result['all_probabilities']
            })
            
    except Exception as e:
        import traceback
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

if __name__ == '__main__':
    print("🚀 Starting Flask server...")
    print(f"📁 Model path: {MODEL_PATH}")
    print(f"📁 Train dir: {TRAIN_DIR}")
    print("🌐 Server will run on http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')