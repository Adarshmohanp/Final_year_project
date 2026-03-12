from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import uuid
from werkzeug.utils import secure_filename
import tempfile
from utils.gradcam import MRIGradCAM
import base64

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Supabase
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Initialize model
MODEL_PATH = 'mri_model.keras'
TRAIN_DIR = '../crop_train'
gradcam = MRIGradCAM(MODEL_PATH, TRAIN_DIR)

UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'dcm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Save temporarily
            filename = secure_filename(file.filename)
            temp_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(temp_path)
            
            # Generate prediction and heatmap
            result = gradcam.generate_heatmap(temp_path)
            
            # Upload images to Supabase Storage
            # Original MRI
            original_filename = f"mri-images/{doctor_id}/{patient_id}/{uuid.uuid4()}_original.jpg"
            supabase.storage.from_('mri-images').upload(
                original_filename,
                base64.b64decode(result['original_image'])
            )
            
            # Heatmap
            heatmap_filename = f"heatmaps/{doctor_id}/{patient_id}/{uuid.uuid4()}_heatmap.jpg"
            supabase.storage.from_('heatmaps').upload(
                heatmap_filename,
                base64.b64decode(result['heatmap_image'])
            )
            
            # Get public URLs
            original_url = supabase.storage.from_('mri-images').get_public_url(original_filename)
            heatmap_url = supabase.storage.from_('heatmaps').get_public_url(heatmap_filename)
            
            # Save record to database
            record = supabase.table('mri_records').insert({
                'patient_id': patient_id,
                'doctor_id': doctor_id,
                'mri_image_url': original_url,
                'heatmap_url': heatmap_url,
                'prediction': result['prediction'],
                'confidence': result['confidence']
            }).execute()
            
            # Clean up temp file
            os.remove(temp_path)
            
            return jsonify({
                'success': True,
                'prediction': result['prediction'],
                'confidence': result['confidence'],
                'original_image': original_url,
                'heatmap_image': heatmap_url,
                'all_probabilities': result['all_probabilities'],
                'record_id': record.data[0]['id']
            }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients', methods=['POST'])
def add_patient():
    try:
        data = request.json
        patient = supabase.table('patients').insert({
            'patient_name': data['patient_name'],
            'patient_age': data.get('patient_age'),
            'patient_gender': data.get('patient_gender'),
            'description': data.get('description'),
            'doctor_id': data['doctor_id']
        }).execute()
        
        return jsonify({'success': True, 'patient': patient.data[0]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/<doctor_id>', methods=['GET'])
def get_patients(doctor_id):
    try:
        patients = supabase.table('patients')\
            .select('*')\
            .eq('doctor_id', doctor_id)\
            .execute()
        return jsonify({'patients': patients.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patient-records/<patient_id>', methods=['GET'])
def get_patient_records(patient_id):
    try:
        records = supabase.table('mri_records')\
            .select('*')\
            .eq('patient_id', patient_id)\
            .order('created_at', desc=True)\
            .execute()
        return jsonify({'records': records.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)