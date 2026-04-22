// Authentication & Enumeration Challenge JavaScript
// VOID PROTOCOL CTF Platform

// User credentials database
const users = {
    'user': {
        password: 'user123',
        role: 'standard',
        redirect: null
    },
    'admin': {
        password: 'admin123',
        role: 'standard',
        redirect: null
    },
    'admin_hidden': {
        password: 'admin857',
        role: 'privileged',
        redirect: 'challenge-auth-enum-dashboard.html'
    }
};

// Login form handler
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const errorMsg = document.getElementById('errorMsg');
    
    // Validate credentials
    let authenticated = false;
    let redirectUrl = null;
    
    // Check user account
    if (username === 'user' && password === 'user123') {
        authenticated = true;
        redirectUrl = users.user.redirect;
    }
    // Check standard admin account
    else if (username === 'admin' && password === 'admin123') {
        authenticated = true;
        redirectUrl = users.admin.redirect;
    }
    // Check hidden admin account (the target for the challenge)
    else if (username === 'admin' && password === 'admin857') {
        authenticated = true;
        redirectUrl = users.admin_hidden.redirect;
    }
    
    if (authenticated) {
        if (redirectUrl) {
            // Redirect to dashboard for hidden admin
            window.location.href = redirectUrl;
        } else {
            // Standard login - show success message
            errorMsg.style.display = 'block';
            errorMsg.style.background = '#23863626';
            errorMsg.style.borderColor = '#238636';
            errorMsg.style.color = '#3fb950';
            errorMsg.textContent = 'Authentication successful. Access granted to standard interface.';
            setTimeout(() => {
                errorMsg.style.display = 'none';
            }, 3000);
        }
    } else {
        // Show error message
        errorMsg.style.display = 'block';
        errorMsg.textContent = 'Authentication failed. Invalid credentials.';
        
        // Shake animation on form
        const form = document.getElementById('loginForm');
        form.classList.remove('shake');
        void form.offsetWidth; // Trigger reflow
        form.classList.add('shake');
    }
});

// Console message for debugging (not part of the challenge)
console.log('Authentication & Enumeration Challenge loaded');
console.log('Hint: The hidden admin password follows the pattern described in the security advisory');
