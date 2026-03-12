-- Create patients table
CREATE TABLE patients (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_name VARCHAR(255) NOT NULL,
    patient_age INTEGER,
    patient_gender VARCHAR(10),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    doctor_id UUID REFERENCES auth.users(id)
);

-- Create mri_records table
CREATE TABLE mri_records (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    mri_image_url TEXT NOT NULL,
    heatmap_url TEXT NOT NULL,
    prediction VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    actual_class VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    doctor_id UUID REFERENCES auth.users(id)
);

-- Create storage buckets
-- Bucket: mri-images (for original MRI images)
-- Bucket: heatmaps (for Grad-CAM outputs)

-- Enable Row Level Security
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE mri_records ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Doctors can view their own patients"
    ON patients FOR ALL
    USING (auth.uid() = doctor_id);

CREATE POLICY "Doctors can view their own records"
    ON mri_records FOR ALL
    USING (auth.uid() = doctor_id);