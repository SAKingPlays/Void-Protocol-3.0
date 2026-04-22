// Dashboard JavaScript for Authentication & Enumeration Challenge
// VOID PROTOCOL CTF Platform

// System configuration and initialization
const config = {
    sessionId: '8X-7294',
    accessLevel: 'CLASSIFIED',
    securityStatus: 'COMPROMISED'
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    console.log('Session ID:', config.sessionId);
    console.log('Access Level:', config.accessLevel);
    console.log('Security Status:', config.securityStatus);
    
    // Add timestamp to logs
    const logEntries = document.querySelectorAll('.log-entry');
    logEntries.forEach(entry => {
        entry.style.opacity = '0';
        entry.style.transform = 'translateX(-20px)';
        setTimeout(() => {
            entry.style.transition = 'all 0.5s ease';
            entry.style.opacity = '1';
            entry.style.transform = 'translateX(0)';
        }, Math.random() * 1000);
    });
});

// Security monitoring function
function monitorSecurity() {
    setInterval(() => {
        const status = document.querySelector('.stat-card:nth-child(3) .value');
        if (status) {
            status.style.opacity = status.style.opacity === '0.5' ? '1' : '0.5';
        }
    }, 2000);
}

monitorSecurity();

// Hidden flag for challenge completion
// Base64 encoded: ZmxhZ3thdXRoZW50aWNhdGlvbl9lbnVtZXJhdGlvbl9zdWNjZXNzfQ==
// This flag is awarded for completing the Authentication & Enumeration challenge
// Decode to reveal: flag{authentication_enumeration_success}

// Legacy system reference code
// DO NOT MODIFY - Used for system integrity verification
const legacyChecksum = 'a7f3b2c1d4e5f6g7h8i9j0k1l2m3n4o5';
