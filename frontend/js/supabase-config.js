// Supabase configuration
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';

// Flag to switch between mock and real data
const USE_MOCK_DATA = false; // Change to false when Supabase is ready

// Initialize Supabase client (but don't fail if not configured)
let supabase = null;
try {
    if (!USE_MOCK_DATA && SUPABASE_URL !== 'YOUR_SUPABASE_URL') {
        supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    }
} catch (error) {
    console.log('Supabase not configured, using mock data');
}

// Mock data (keep this in the same file)
// const mockPatients = [
//     {
//         id: '1',
//         patient_name: 'John Doe',
//         patient_age: 45,
//         patient_gender: 'Male',
//         description: 'Patient with history of headaches',
//         created_at: '2024-03-10T10:00:00Z'
//     },
//     {
//         id: '2',
//         patient_name: 'Jane Smith',
//         patient_age: 52,
//         patient_gender: 'Female',
//         description: 'Follow-up after previous treatment',
//         created_at: '2024-03-09T14:30:00Z'
//     },
//     {
//         id: '3',
//         patient_name: 'Robert Johnson',
//         patient_age: 38,
//         patient_gender: 'Male',
//         description: 'New patient with MRI scan',
//         created_at: '2024-03-08T09:15:00Z'
//     }
// ];

// const mockHistory = [
//     {
//         id: '101',
//         patient_id: '1',
//         patients: { patient_name: 'John Doe' },
//         prediction: 'Glioma',
//         confidence: 87.5,
//         created_at: '2024-03-10T10:30:00Z',
//         mri_image_url: 'https://via.placeholder.com/300x300?text=MRI+1',
//         heatmap_url: 'https://via.placeholder.com/300x300?text=Heatmap+1'
//     },
//     // ... more mock data
// ];