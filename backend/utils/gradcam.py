import tensorflow as tf
import numpy as np
import cv2
from tensorflow.keras.preprocessing import image

class MRIGradCAM:
    def __init__(self, model_path, train_dir):
        self.model = tf.keras.models.load_model(model_path)
        self.categories = sorted([d for d in os.listdir(train_dir) 
                                 if os.path.isdir(os.path.join(train_dir, d))])
        self.res = 240
        self.target_layer_name = 'block7a_project_conv'
    
    def generate_heatmap(self, img_path):
        # Load and preprocess image
        img = image.load_img(img_path, target_size=(self.res, self.res))
        x_orig = image.img_to_array(img)
        x_input = np.expand_dims(x_orig, axis=0)
        
        # Get target layer
        target_layer = self.model.get_layer(self.target_layer_name)
        
        # Create Grad model
        grad_model = tf.keras.models.Model(
            [self.model.inputs], 
            [target_layer.output, self.model.output]
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
        
        if np.max(heatmap) != 0:
            heatmap = heatmap / np.max(heatmap)
        heatmap = heatmap.numpy()
        
        # Resize and colorize heatmap
        heatmap_resized = cv2.resize(heatmap, (self.res, self.res))
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
        
        # Superimpose
        img_display = x_orig.astype('uint8')
        superimposed = cv2.addWeighted(img_display, 0.6, heatmap_color, 0.4, 0)
        
        # Convert to base64 for easy transfer
        _, buffer_original = cv2.imencode('.jpg', cv2.cvtColor(img_display, cv2.COLOR_RGB2BGR))
        _, buffer_heatmap = cv2.imencode('.jpg', cv2.cvtColor(superimposed, cv2.COLOR_RGB2BGR))
        
        import base64
        original_b64 = base64.b64encode(buffer_original).decode('utf-8')
        heatmap_b64 = base64.b64encode(buffer_heatmap).decode('utf-8')
        
        return {
            'prediction': self.categories[pred_idx],
            'confidence': confidence * 100,
            'original_image': original_b64,
            'heatmap_image': heatmap_b64,
            'all_probabilities': {
                cat: float(predictions[0][i]) * 100 
                for i, cat in enumerate(self.categories)
            }
        }