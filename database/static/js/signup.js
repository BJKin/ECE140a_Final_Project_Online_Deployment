// DOM elements
const signupForm = document.getElementById('signupForm');
const signinBtn = document.getElementById('signinBtn');



document.addEventListener('DOMContentLoaded', () => {

    // Handle form submission
    signupForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const location = document.getElementById('location').value;
        

        if (!name || !email || !password || !location) {
            alert('Please fill in all required fields');
            return;
        }
        
        const formData = new FormData();
        formData.append('name', name);
        formData.append('email', email);
        formData.append('password', password);
        formData.append('location', location || '');
        
        try {
            const response = await fetch('/signup', {method: 'POST', body: formData});
            if (response.ok) {
                const redirectUrl = response.redirected ? response.url : '/profile';
                window.location.href = redirectUrl;
            } else {
                const errorText = await response.text();
                if (errorText.includes('error')) {
                    document.body.innerHTML = errorText;
                } else {
                    alert('Signup failed. Please try again.');
                }
            }
        } catch (error) {
            console.error('Signup error:', error);
            alert('An error occurred during signup. Please try again.');
        }
    });
    
    // Handle sign in button click
    signinBtn.addEventListener('click', function() {
        window.location.href = '/login';
    });
    
    // Prevent double submissions
    const preventDoubleSubmission = () => {
        const submitButtons = document.querySelectorAll('button[type="submit"]');
        submitButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                const form = this.closest('form');
                if (form && form.dataset.submitting === 'true') {
                    e.preventDefault();
                    return;
                }
                
                if (form) {
                    form.dataset.submitting = 'true';
                    setTimeout(() => {
                        form.dataset.submitting = 'false';
                    }, 2000);
                }
            });
        });
    };
    
    preventDoubleSubmission();
});