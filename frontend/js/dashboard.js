// frontend/js/dashboard.js - SIMPLIFIED WORKING VERSION

// ============= MOCK DATA =============
const mockPatients = [
    {
        id: '1',
        patient_name: 'John Doe',
        patient_age: 45,
        patient_gender: 'Male',
        description: 'Patient with history of headaches',
        created_at: '2024-03-10T10:00:00Z'
    },
    {
        id: '2',
        patient_name: 'Jane Smith',
        patient_age: 52,
        patient_gender: 'Female',
        description: 'Follow-up after previous treatment',
        created_at: '2024-03-09T14:30:00Z'
    },
    {
        id: '3',
        patient_name: 'Robert Johnson',
        patient_age: 38,
        patient_gender: 'Male',
        description: 'New patient with MRI scan',
        created_at: '2024-03-08T09:15:00Z'
    }
];

const mockHistory = [
    {
        id: '101',
        patient_id: '1',
        patient_name: 'John Doe',
        prediction: 'Glioma',
        confidence: 87.5,
        created_at: '2024-03-10T10:30:00Z',
        mri_image_url: 'https://via.placeholder.com/300x300?text=Original+MRI',
        heatmap_url: 'https://via.placeholder.com/300x300?text=Grad-CAM+Heatmap'
    },
    {
        id: '102',
        patient_id: '2',
        patient_name: 'Jane Smith',
        prediction: 'Meningioma',
        confidence: 92.3,
        created_at: '2024-03-09T15:00:00Z',
        mri_image_url: 'https://via.placeholder.com/300x300?text=Original+MRI',
        heatmap_url: 'https://via.placeholder.com/300x300?text=Grad-CAM+Heatmap'
    },
    {
        id: '103',
        patient_id: '3',
        patient_name: 'Robert Johnson',
        prediction: 'No Tumor',
        confidence: 95.1,
        created_at: '2024-03-08T11:00:00Z',
        mri_image_url: 'https://via.placeholder.com/300x300?text=Original+MRI',
        heatmap_url: 'https://via.placeholder.com/300x300?text=Grad-CAM+Heatmap'
    }
];

const mockAnalysisResult = {
    prediction: 'Glioma',
    confidence: 87.5,
    original_image: 'https://via.placeholder.com/500x500?text=Original+MRI',
    heatmap_image: 'https://via.placeholder.com/500x500?text=Grad-CAM+Heatmap',
    all_probabilities: {
        'Glioma': 87.5,
        'Meningioma': 8.2,
        'Pituitary': 3.1,
        'No Tumor': 1.2
    }
};

// ============= STATE =============
let currentUser = { 
    id: 'mock-doctor-1', 
    user_metadata: { full_name: 'Smith' } 
};
let currentPatientId = null;
let currentAnalysisResult = null;
let probabilityChart = null;

// ============= INITIALIZATION =============
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded');
    
    // Set doctor name
    const userNameEl = document.getElementById('user-name');
    if (userNameEl) {
        userNameEl.textContent = 'Dr. Smith';
    }
    
    // Load patients
    loadPatients();
    
    // Setup navigation
    setupNavigation();
    
    // Setup form handlers
    setupForms();
});

// ============= NAVIGATION =============
function setupNavigation() {
    // Get all menu items
    const menuItems = document.querySelectorAll('.nav-menu li');
    
    // Add click handlers to each
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Remove active class from all menu items
            menuItems.forEach(i => i.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Get the section name from the text content
            const text = this.textContent.trim();
            let section = '';
            
            if (text.includes('Patients')) section = 'patients';
            else if (text.includes('New Analysis')) section = 'new-analysis';
            else if (text.includes('History')) section = 'history';
            else if (text.includes('Profile')) section = 'profile';
            
            // Show the corresponding section
            showSection(section);
        });
    });
}

function showSection(section) {
    console.log('Showing section:', section);
    
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(s => {
        s.classList.remove('active');
    });
    
    // Show selected section
    const sectionEl = document.getElementById(section + '-section');
    if (sectionEl) {
        sectionEl.classList.add('active');
        
        // Load data if needed
        if (section === 'history') {
            loadHistory();
        } else if (section === 'new-analysis') {
            loadPatientsForSelect();
        } else if (section === 'profile') {
            loadProfile();
        }
    }
}

// ============= PATIENTS =============
function loadPatients() {
    const grid = document.getElementById('patients-grid');
    if (!grid) return;
    
    if (mockPatients.length === 0) {
        grid.innerHTML = '<div class="empty-state">No patients yet</div>';
        return;
    }
    
    let html = '';
    mockPatients.forEach(patient => {
        html += `
            <div class="patient-card">
                <h3>${patient.patient_name}</h3>
                <p>👤 Age: ${patient.patient_age || 'N/A'} | Gender: ${patient.patient_gender || 'N/A'}</p>
                <p>📅 Added: ${new Date(patient.created_at).toLocaleDateString()}</p>
                ${patient.description ? `<p class="description">📝 ${patient.description.substring(0, 50)}</p>` : ''}
                <button onclick="viewPatientRecords('${patient.id}')" class="view-records">
                    View Records
                </button>
            </div>
        `;
    });
    
    grid.innerHTML = html;
}

function loadPatientsForSelect() {
    const select = document.getElementById('patient-select');
    if (!select) return;
    
    let options = '<option value="">Select a patient</option>';
    mockPatients.forEach(p => {
        options += `<option value="${p.id}">${p.patient_name}</option>`;
    });
    
    select.innerHTML = options;
}

// ============= NEW ANALYSIS =============
function setupForms() {
    // Analysis form
    const analysisForm = document.getElementById('analysis-form');
    if (analysisForm) {
        analysisForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleAnalysis();
        });
    }
    
    // Add patient form
    const addPatientForm = document.getElementById('add-patient-form');
    if (addPatientForm) {
        addPatientForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleAddPatient();
        });
    }
    
    // File upload
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('mri-image');
    
    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#3498db';
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = '#ddd';
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#ddd';
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                updateUploadAreaText(e.dataTransfer.files[0].name);
            }
        });
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                updateUploadAreaText(fileInput.files[0].name);
            }
        });
    }
}

// function updateUploadAreaText(filename) {
//     const uploadArea = document.getElementById('upload-area');
//     if (uploadArea) {
//         uploadArea.innerHTML = `<p>📁 ${filename}</p><small>Click or drag to change</small>`;
//     }
// }

// function updateUploadAreaText(filename) {
//     const uploadArea = document.getElementById('upload-area');
//     const fileInput = document.getElementById('mri-image');

//     if (uploadArea && fileInput) {
//         uploadArea.innerHTML = `
//             <input type="file" id="mri-image" accept="image/*" style="display:none">
//             <p>📁 ${filename}</p>
//             <small>Click or drag to change</small>
//         `;

//         // Reattach file input
//         uploadArea.appendChild(fileInput);
//     }
// }


function updateUploadAreaText(filename) {
    const uploadArea = document.getElementById('upload-area');

    if (uploadArea) {
        const textElement = uploadArea.querySelector("p");
        if (textElement) {
            textElement.textContent = `📁 ${filename}`;
        }
    }
}

// ============= NEW ANALYSIS WITH REAL MODEL =============

// ============= TEST MODEL WITH UPLOAD =============
async function handleAnalysis() {
    const patientId = document.getElementById('patient-select').value;
    const fileInput = document.getElementById('mri-image');
    const notes = document.getElementById('analysis-notes').value;
    
    if (!patientId) {
        alert('Please select a patient');
        return;
    }
    
    if (!fileInput.files.length) {
        alert('Please select an MRI image');
        return;
    }
    
    // Show loading state
    const submitBtn = document.querySelector('#analysis-form button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '🔬 Analyzing with AI...';
    submitBtn.disabled = true;
    
    // Show loading indicator in results area
    const resultsDiv = document.getElementById('analysis-results');
    resultsDiv.classList.remove('hidden');
    resultsDiv.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <div style="font-size: 48px; margin-bottom: 20px;">🔬</div>
            <h3>Analyzing MRI Image...</h3>
            <p>Please wait while the AI model processes the image</p>
            <div style="width: 100%; height: 4px; background: #f0f0f0; margin-top: 20px;">
                <div style="width: 0%; height: 100%; background: #3498db; animation: loading 2s infinite;"></div>
            </div>
        </div>
    `;
    

    console.log("Selected file:", fileInput.files[0]);
    // Create form data
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    try {
        // Call your Flask backend
        console.log('Sending request to backend...');
        const response = await fetch('http://localhost:5000/api/predict', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        // generateAIExplanation(result);
        console.log('Received response:', result);
        
        if (!response.ok) {
            throw new Error(result.error || 'Unknown error');
        }
        
        if (!result.success) {
            throw new Error('Prediction failed');
        }
        
        // Store result
        currentAnalysisResult = result;
        result.all_probabilities = result.all_probabilities || {};
        console.log(currentAnalysisResult);
        currentPatientId = patientId;
        
        // Convert base64 to data URLs for display
        if (result.original_image) {
            result.original_image = 'data:image/jpeg;base64,' + result.original_image;
            result.heatmap_image = 'data:image/jpeg;base64,' + result.heatmap_image;
        }
        
        // Display results
        displayRealResults(result);
        generateAIExplanation(result);
    } catch (error) {
        console.error('Analysis failed:', error);
        
        // Show error message
        resultsDiv.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #e74c3c;">
                <div style="font-size: 48px; margin-bottom: 20px;">❌</div>
                <h3>Analysis Failed</h3>
                <p>${error.message}</p>
                <button onclick="retryAnalysis()" style="margin-top: 20px; padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    Try Again
                </button>
            </div>
        `;
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

// Display real results from model
function displayRealResults(result) {
    const resultsDiv = document.getElementById('analysis-results');
    
    // document.getElementById("ai-explanation").innerText = result.explanation;
    let coverageLabel = "Estimated Tumor Coverage";

    if(result.prediction.toLowerCase().replace(" ", "_") === "no_tumor"){
        coverageLabel = "Model Activation Coverage";
    }
    // Create results HTML
    let probabilitiesHtml = '';
    // for (const [className, prob] of Object.entries(result.all_probabilities)) {
    //     const color = getProbabilityColor(className);
    //     probabilitiesHtml += `
    //         <div style="margin: 10px 0;">
    //             <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
    //                 <span>${className}</span>
    //                 <span style="font-weight: bold; color: ${color};">${prob.toFixed(1)}%</span>
    //             </div>
    //             <div style="width: 100%; height: 8px; background: #f0f0f0; border-radius: 4px;">
    //                 <div style="width: ${prob}%; height: 100%; background: ${color}; border-radius: 4px;"></div>
    //             </div>
    //         </div>
    //     `;
    // }
    
    if (result.all_probabilities) {
    for (const [className, prob] of Object.entries(result.all_probabilities)) {
        const color = getProbabilityColor(className);
        probabilitiesHtml += `
            <div style="margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span>${className}</span>
                    <span style="font-weight: bold; color: ${color};">${prob.toFixed(1)}%</span>
                </div>
                <div style="width: 100%; height: 8px; background: #f0f0f0; border-radius: 4px;">
                    <div style="width: ${prob}%; height: 100%; background: ${color}; border-radius: 4px;"></div>
                </div>
            </div>
        `;
    }
}



    resultsDiv.innerHTML = `
        <h3>Analysis Results</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
            <div class="result-card">
                <h4>Original MRI</h4>
                <img src="${result.original_image}" style="width: 100%; border-radius: 8px;">
            </div>
            <div class="result-card">
                <h4>Grad-CAM Heatmap</h4>
                <img src="${result.heatmap_image}" style="width: 100%; border-radius: 8px;">
            </div>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 20px;">
                <span class="prediction-badge ${result.prediction.toLowerCase().replace(' ', '_')}" 
                      style="font-size: 18px; padding: 10px 20px;">
                    ${result.prediction}
                </span>
                <div style="flex: 1;">
                    <div style="font-size: 14px; color: #666;">Confidence</div>
                    <div style="font-size: 24px; font-weight: bold; color: ${getProbabilityColor(result.prediction)};">
                        ${result.confidence}%
                    </div>
                </div>
            </div>
            
            <h4><u>Model Attention Analysis</u></h4>

            <div style="margin-bottom:15px;">
                <strong>Primary Activation Region:</strong>
                ${result.tumor_location || "Not detected"}
            </div>

            <div style="margin-bottom:15px;">
                <strong>${coverageLabel}:</strong>
                ${result.tumor_coverage != null ? result.tumor_coverage.toFixed(2) + "%" : "N/A"}
            </div>

            <hr style="margin:15px 0;">

            <h4>All Probabilities</h4>
            ${probabilitiesHtml}

            <hr style="margin:20px 0;">

            <h4>AI Clinical Explanation</h4>
            <div id="ai-explanation" style="
                background:#ffffff;
                padding:15px;
                border-radius:8px;
                border-left:4px solid #3498db;
                font-size:14px;
                line-height:1.6;
            ">
                Generating AI explanation...
            </div>
        </div>
        
        <div style="display: flex; gap: 10px; justify-content: flex-end;">
            <button onclick="saveAnalysis()" class="btn-success">
                Save to Records
            </button>
            <button onclick="resetAnalysis()" class="btn-secondary">
                New Analysis
            </button>
        </div>
    `;
}

// Helper function for colors
function getProbabilityColor(className) {
    const colors = {
        'glioma': '#f39c12',
        'meningioma': '#3498db',
        'pituitary': '#9b59b6',
        'no_tumor': '#27ae60'
    };
    return colors[className.toLowerCase()] || '#95a5a6';
}

// // Enable zoom & pan on an image
// function enableZoomOnImage(imgId) {
//     const elem = document.getElementById(imgId);
//     if (!elem) return;
    
//     const panzoom = Panzoom(elem, {
//         maxScale: 5,
//         minScale: 1,
//         contain: 'inside',
//         cursor: 'grab',
//         step: 0.1
//     });

//     // Enable mouse wheel zoom
//     elem.parentElement.addEventListener('wheel', panzoom.zoomWithWheel);
// }



// Retry function
function retryAnalysis() {
    document.getElementById('analysis-results').classList.add('hidden');
}

// Reset function
function resetAnalysis() {
    document.getElementById('analysis-form').reset();
    document.getElementById('analysis-results').classList.add('hidden');
    document.getElementById('upload-area').innerHTML = '<p>Drag & drop or click to upload</p>';
}

/////////////////////////////


function displayAnalysisResults(result) {
    const resultsDiv = document.getElementById('analysis-results');
    if (!resultsDiv) return;
    
    resultsDiv.classList.remove('hidden');
    
    // Set images
    const originalImg = document.getElementById('result-original');
    const heatmapImg = document.getElementById('result-heatmap');
    
    if (originalImg) originalImg.src = result.original_image;
    if (heatmapImg) heatmapImg.src = result.heatmap_image;
    
    // Set prediction
    const badge = document.getElementById('prediction-label');
    if (badge) {
        badge.textContent = `${result.prediction} (${result.confidence.toFixed(1)}%)`;
        badge.className = `prediction-badge ${result.prediction.toLowerCase().replace(' ', '_')}`;
    }
    
    // Set confidence bar
    const confidenceFill = document.getElementById('confidence-fill');
    if (confidenceFill) {
        confidenceFill.style.width = `${result.confidence}%`;
    }
    
    // Create chart
    createProbabilityChart(result.all_probabilities);
}

function createProbabilityChart(probabilities) {
    const canvas = document.getElementById('probChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    if (probabilityChart) {
        probabilityChart.destroy();
    }
    
    probabilityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(probabilities),
            datasets: [{
                label: 'Confidence (%)',
                data: Object.values(probabilities),
                backgroundColor: [
                    '#f39c12', '#3498db', '#9b59b6', '#27ae60'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function saveAnalysis() {
    alert('✅ Analysis saved successfully!');
    
    // Clear form
    document.getElementById('analysis-form').reset();
    document.getElementById('analysis-results').classList.add('hidden');
    
    const uploadArea = document.getElementById('upload-area');
    if (uploadArea) {
        uploadArea.innerHTML = '<p>Drag & drop or click to upload</p>';
    }
}

// ============= HISTORY =============
function loadHistory() {
    const grid = document.getElementById('history-grid');
    if (!grid) return;
    
    if (mockHistory.length === 0) {
        grid.innerHTML = '<div class="empty-state">No history yet</div>';
        return;
    }
    
    let html = '';
    mockHistory.forEach(record => {
        html += `
            <div class="history-card">
                <img src="${record.heatmap_url}" alt="Heatmap">
                <div class="history-info">
                    <h4>${record.patient_name}</h4>
                    <p class="date">📅 ${new Date(record.created_at).toLocaleDateString()}</p>
                    <span class="prediction ${record.prediction.toLowerCase().replace(' ', '_')}">
                        ${record.prediction}
                    </span>
                    <p class="confidence">📊 ${record.confidence}% confidence</p>
                    <button onclick="viewRecordDetails('${record.id}')" class="btn-small">
                        View Details
                    </button>
                </div>
            </div>
        `;
    });
    
    grid.innerHTML = html;
    
    // Setup filters
    setupFilters();
}

function setupFilters() {
    const searchInput = document.getElementById('search-history');
    const filterSelect = document.getElementById('filter-prediction');
    
    if (searchInput) {
        searchInput.addEventListener('input', filterHistory);
    }
    if (filterSelect) {
        filterSelect.addEventListener('change', filterHistory);
    }
}

function filterHistory() {
    const searchTerm = document.getElementById('search-history').value.toLowerCase();
    const filterValue = document.getElementById('filter-prediction').value.toLowerCase();
    
    const filtered = mockHistory.filter(record => {
        const matchesSearch = record.patient_name.toLowerCase().includes(searchTerm);
        const matchesFilter = !filterValue || record.prediction.toLowerCase() === filterValue;
        return matchesSearch && matchesFilter;
    });
    
    // Display filtered results
    const grid = document.getElementById('history-grid');
    if (!grid) return;
    
    if (filtered.length === 0) {
        grid.innerHTML = '<div class="empty-state">No matching records</div>';
        return;
    }
    
    let html = '';
    filtered.forEach(record => {
        html += `
            <div class="history-card">
                <img src="${record.heatmap_url}" alt="Heatmap">
                <div class="history-info">
                    <h4>${record.patient_name}</h4>
                    <p class="date">📅 ${new Date(record.created_at).toLocaleDateString()}</p>
                    <span class="prediction ${record.prediction.toLowerCase().replace(' ', '_')}">
                        ${record.prediction}
                    </span>
                    <p class="confidence">📊 ${record.confidence}% confidence</p>
                    <button onclick="viewRecordDetails('${record.id}')" class="btn-small">
                        View Details
                    </button>
                </div>
            </div>
        `;
    });
    
    grid.innerHTML = html;
}

// ============= PATIENT MODAL =============
function showAddPatientModal() {
    const modal = document.getElementById('patient-modal');
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal() {
    const modal = document.getElementById('patient-modal');
    if (modal) {
        modal.classList.remove('active');
    }
}

function handleAddPatient() {
    const name = document.getElementById('patient-name').value;
    const age = document.getElementById('patient-age').value;
    const gender = document.getElementById('patient-gender').value;
    const description = document.getElementById('patient-description').value;
    
    if (!name) {
        alert('Please enter patient name');
        return;
    }
    
    // Add to mock data
    const newPatient = {
        id: String(mockPatients.length + 1),
        patient_name: name,
        patient_age: age || null,
        patient_gender: gender || null,
        description: description || null,
        created_at: new Date().toISOString()
    };
    
    mockPatients.push(newPatient);
    
    alert('✅ Patient added successfully!');
    closeModal();
    
    // Refresh
    loadPatients();
    loadPatientsForSelect();
}

// ============= VIEW RECORDS =============
function viewPatientRecords(patientId) {
    const patient = mockPatients.find(p => p.id === patientId);
    const records = mockHistory.filter(r => r.patient_id === patientId);
    
    if (!patient) return;
    
    let recordsHtml = '';
    if (records.length === 0) {
        recordsHtml = '<p>No records found</p>';
    } else {
        records.forEach(record => {
            recordsHtml += `
                <div class="record-item">
                    <img src="${record.heatmap_url}" alt="Heatmap">
                    <div class="record-details">
                        <p><strong>${record.prediction}</strong> (${record.confidence}%)</p>
                        <p>📅 ${new Date(record.created_at).toLocaleDateString()}</p>
                        <button onclick="viewFullImage('${record.mri_image_url}', '${record.heatmap_url}')">
                            View Images
                        </button>
                    </div>
                </div>
            `;
        });
    }
    
    const modal = document.getElementById('patient-modal');
    if (modal) {
        const content = modal.querySelector('.modal-content');
        content.innerHTML = `
            <span class="close" onclick="closeModal()">&times;</span>
            <h3>${patient.patient_name}'s Records</h3>
            <p>👤 Age: ${patient.patient_age || 'N/A'} | Gender: ${patient.patient_gender || 'N/A'}</p>
            ${patient.description ? `<p>📝 ${patient.description}</p>` : ''}
            <div class="records-list">
                ${recordsHtml}
            </div>
        `;
        modal.classList.add('active');
    }
}

function viewRecordDetails(recordId) {
    const record = mockHistory.find(r => r.id === recordId);
    if (record) {
        viewFullImage(record.mri_image_url, record.heatmap_url);
    }
}

function viewFullImage(originalUrl, heatmapUrl) {
    const modal = document.getElementById('patient-modal');
    if (modal) {
        const content = modal.querySelector('.modal-content');
        content.innerHTML = `
            <span class="close" onclick="closeModal()">&times;</span>
            <h3>MRI Analysis Images</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                <div>
                    <h4>Original MRI</h4>
                    <img src="${originalUrl}" style="width: 100%; border-radius: 8px;">
                </div>
                <div>
                    <h4>Grad-CAM Heatmap</h4>
                    <img src="${heatmapUrl}" style="width: 100%; border-radius: 8px;">
                </div>
            </div>
        `;
        modal.classList.add('active');
    }
}


// function viewFullImage(originalUrl, heatmapUrl) {
//     const modal = document.getElementById('patient-modal');
//     if (!modal) return;

//     const content = modal.querySelector('.modal-content');
//     content.innerHTML = `
//         <span class="close" onclick="closeModal()">&times;</span>
//         <h3>MRI Analysis Images</h3>
//         <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
//             <div id="original-container">
//                 <h4>Original MRI</h4>
//                 <img id="original-img" src="${originalUrl}" style="max-width: 100%; display: block; border-radius: 8px;">
//             </div>
//             <div id="heatmap-container">
//                 <h4>Grad-CAM Heatmap</h4>
//                 <img id="heatmap-img" src="${heatmapUrl}" style="width: 100%; border-radius: 8px;">
//             </div>
//         </div>
//     `;
//     modal.classList.add('active');

//     // Enable zoom & pan
//     enableZoomOnImage('original-img');
//     enableZoomOnImage('heatmap-img');
// }


// function viewFullImage(originalUrl, heatmapUrl) {
//     const modal = document.getElementById('patient-modal');
//     if (!modal) return;

//     const content = modal.querySelector('.modal-content');
//     content.innerHTML = `
//         <span class="close" onclick="closeModal()">&times;</span>
//         <h3>MRI Analysis Images</h3>
//         <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
//             <div id="original-container" style="overflow: hidden; border: 1px solid #ddd; border-radius: 8px;">
//                 <h4>Original MRI</h4>
//                 <img id="original-img" src="${originalUrl}" style="display: block; max-width: 100%; border-radius: 8px;">
//             </div>
//             <div id="heatmap-container" style="overflow: hidden; border: 1px solid #ddd; border-radius: 8px;">
//                 <h4>Grad-CAM Heatmap</h4>
//                 <img id="heatmap-img" src="${heatmapUrl}" style="display: block; max-width: 100%; border-radius: 8px;">
//             </div>
//         </div>
//     `;
//     modal.classList.add('active');

//     // Enable zoom & pan
//     enableZoomOnImage('original-img');
//     enableZoomOnImage('heatmap-img');
// }



// ============= PROFILE =============
// ============= PROFILE =============
function loadProfile() {
    console.log('Loading profile...');
    const profileSection = document.getElementById('profile-section');
    if (!profileSection) {
        console.error('Profile section not found!');
        return;
    }
    
    profileSection.innerHTML = `
        <h2>Doctor Profile</h2>
        <div style="background: white; padding: 30px; border-radius: 15px; margin-top: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <div style="font-size: 80px;">👨‍⚕️</div>
                <h3>Dr. Smith</h3>
                <p style="color: #666; margin-top: 5px;">Neurosurgeon</p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px;">
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4 style="color: #3498db; font-size: 32px; margin-bottom: 5px;">${mockPatients.length}</h4>
                    <p style="color: #666; font-size: 14px;">Total Patients</p>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4 style="color: #3498db; font-size: 32px; margin-bottom: 5px;">${mockHistory.length}</h4>
                    <p style="color: #666; font-size: 14px;">Total Analyses</p>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4 style="color: #3498db; font-size: 32px; margin-bottom: 5px;">2024</h4>
                    <p style="color: #666; font-size: 14px;">Member Since</p>
                </div>
            </div>
            
            <div style="border-top: 2px solid #f0f0f0; padding-top: 20px;">
                <h4 style="margin-bottom: 15px;">📋 Recent Activity</h4>
                ${mockHistory.length > 0 ? mockHistory.slice(0, 3).map(record => `
                    <div style="padding: 12px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #2c3e50;">${record.patient_name}</strong>
                            <span class="prediction-badge-small" style="background: ${getPredictionColor(record.prediction)}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; margin-left: 10px;">
                                ${record.prediction}
                            </span>
                        </div>
                        <div>
                            <span style="color: #666; font-size: 12px;">${new Date(record.created_at).toLocaleDateString()}</span>
                            <span style="color: #3498db; font-weight: bold; margin-left: 10px;">${record.confidence}%</span>
                        </div>
                    </div>
                `).join('') : '<p style="color: #999; text-align: center; padding: 20px;">No recent activity</p>'}
            </div>
            
            <div style="margin-top: 30px; background: #f8f9fa; padding: 20px; border-radius: 10px;">
                <h4 style="margin-bottom: 15px;">⚙️ Account Settings</h4>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                    <div>
                        <label style="color: #666; font-size: 12px;">Email</label>
                        <p style="font-weight: 500;">doctor.smith@hospital.com</p>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">Hospital</label>
                        <p style="font-weight: 500;">City Medical Center</p>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">Specialization</label>
                        <p style="font-weight: 500;">Neuroradiology</p>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">License #</label>
                        <p style="font-weight: 500;">MD-2024-0123</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Helper function for prediction colors
function getPredictionColor(prediction) {
    const colors = {
        'Glioma': '#f39c12',
        'Meningioma': '#3498db',
        'Pituitary': '#9b59b6',
        'No Tumor': '#27ae60'
    };
    return colors[prediction] || '#95a5a6';
}


async function generateAIExplanation(result){

    try{

        const response = await fetch(
            "http://localhost:5000/api/gemini-explain",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(result)
            }
        );

        const data = await response.json();

        document.getElementById("ai-explanation").innerText =
        data.explanation;

    }catch(error){

        console.error("Gemini error:", error);

        document.getElementById("ai-explanation").innerText =
        "AI explanation unavailable.";

    }
}

// Make functions globally available for onclick handlers
window.showAddPatientModal = showAddPatientModal;
window.closeModal = closeModal;
window.viewPatientRecords = viewPatientRecords;
window.viewRecordDetails = viewRecordDetails;
window.viewFullImage = viewFullImage;
window.saveAnalysis = saveAnalysis;
window.logout = function() {
    window.location.href = '/';
};