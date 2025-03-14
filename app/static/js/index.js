const signupButton = document.querySelector('.signup-button');
const loginButton = document.querySelector('.login-button');
const getStartedButton = document.querySelector('.getStarted-button');

document.addEventListener("DOMContentLoaded", function(){
    
    // Handle signup button click
    signupButton.addEventListener("click", function(event) {
        event.preventDefault();
        setTimeout(() => {
            window.location.href = '/signup';
        }, 300);
    });

    // Handle login button click
    loginButton.addEventListener("click", function(event) {
        event.preventDefault();
        setTimeout(() => {
            window.location.href = '/login';
        }, 300);
    });

    // Handle get started button click
    getStartedButton.addEventListener("click", function(event) {
        event.preventDefault();
        setTimeout(() => {
            window.location.href = '/signup';
        }, 300);
    });

    // Check if user is authenticated
    function checkAuthentication() {
        const hasCookie = document.cookie.includes('sessionId');
        
        if (hasCookie) {
            // Modify signup button behavior when authenticated
            signupButton.removeEventListener("click", signupButton.onclick);
            signupButton.addEventListener("click", function(event) {
                event.preventDefault();
                window.location.href = '/profile';
            });

            // Modify login button behavior when authenticated
            loginButton.removeEventListener("click", loginButton.onclick);
            loginButton.addEventListener("click", function(event) {
                event.preventDefault();
                window.location.href = '/profile';
            });
        }
    }

    // Check authentication status when page loads
    checkAuthentication();
});