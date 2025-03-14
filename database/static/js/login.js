const loginForm = document.getElementById("loginForm");
const signupBtn = document.getElementById("signupBtn");

document.addEventListener("DOMContentLoaded", function() {
    
    // Handle signup button click
    signupBtn.addEventListener("click", function() {
        window.location.href = '/signup';
    });
    
    // Handle form submission
    loginForm.addEventListener("submit", async function(event) {
        event.preventDefault();
        
        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;
        
        if (!username || !password) {
            alert("Please fill in all fields");
            return;
        }
        
        try {
            const formData = new FormData();
            formData.append("username", username);
            formData.append("password", password);
            
            const response = await fetch('/login', {method: 'POST', body: formData});
            
            if (response.ok) {
                const redirectUrl = response.redirected ? response.url : '/profile';
                window.location.href = redirectUrl;
            } else {
                const errorText = await response.text();
                if (errorText.includes('error')) {
                    document.body.innerHTML = errorText;
                } else {
                    alert("Login failed. Please check your credentials.");
                }
            }
        } catch (error) {
            alert("An error occurred during login. Please try again.");
        }
    });
});