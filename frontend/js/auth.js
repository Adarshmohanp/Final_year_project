// Auth state management
let currentUser = null;

// Check if user is logged in
async function checkUser() {
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
        currentUser = user;
        window.location.href = '/dashboard.html';
    }
}

// Switch between login and signup tabs
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    if (tab === 'login') {
        document.getElementById('login-form').classList.add('active-form');
        document.getElementById('signup-form').classList.remove('active-form');
    } else {
        document.getElementById('signup-form').classList.add('active-form');
        document.getElementById('login-form').classList.remove('active-form');
    }
}

// Handle login
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const { data, error } = await supabase.auth.signInWithPassword({
            email: email,
            password: password
        });
        
        if (error) throw error;
        
        currentUser = data.user;
        window.location.href = '/dashboard.html';
    } catch (error) {
        alert('Login failed: ' + error.message);
    }
});

// Handle signup
document.getElementById('signup-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const name = document.getElementById('signup-name').value;
    
    try {
        const { data, error } = await supabase.auth.signUp({
            email: email,
            password: password,
            options: {
                data: {
                    full_name: name
                }
            }
        });
        
        if (error) throw error;
        
        alert('Signup successful! Please check your email for verification.');
    } catch (error) {
        alert('Signup failed: ' + error.message);
    }
});

// Initialize
checkUser();