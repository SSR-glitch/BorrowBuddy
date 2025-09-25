
document.addEventListener('DOMContentLoaded', function() {

    // Password Visibility Toggle
    const passwordToggles = document.querySelectorAll('.password-toggle-icon');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const passwordField = toggle.previousElementSibling;
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                toggle.textContent = '🙈';
            } else {
                passwordField.type = 'password';
                toggle.textContent = '👁️';
            }
        });
    });

    // Mobile Navigation Toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }

    // Form Validation
    const signupForm = document.querySelector('#signup-form');
    const signinForm = document.querySelector('#signin-form');

    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            if (!validateSignupForm()) {
                e.preventDefault();
            }
        });
    }

    if (signinForm) {
        signinForm.addEventListener('submit', function(e) {
            if (!validateSigninForm()) {
                e.preventDefault();
            }
        });
    }

    function validateSignupForm() {
        let isValid = true;
        // Reset errors
        document.querySelectorAll('.error-message').forEach(el => el.style.display = 'none');

        // Username validation
        const username = document.querySelector('#username');
        if (username.value.trim() === '') {
            showError('username-error', 'Username is required.');
            isValid = false;
        }

        // Email validation
        const email = document.querySelector('#email');
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(email.value)) {
            showError('email-error', 'Please enter a valid email address.');
            isValid = false;
        }

        // Password validation
        const password = document.querySelector('#password');
        if (password.value.length < 8) {
            showError('password-error', 'Password must be at least 8 characters long.');
            isValid = false;
        }

        // Confirm Password validation
        const confirmPassword = document.querySelector('#confirm-password');
        if (password.value !== confirmPassword.value) {
            showError('confirm-password-error', 'Passwords do not match.');
            isValid = false;
        }

        return isValid;
    }

    function validateSigninForm() {
        let isValid = true;
        // Reset errors
        document.querySelectorAll('.error-message').forEach(el => el.style.display = 'none');

        // Email validation
        const email = document.querySelector('#email');
        if (email.value.trim() === '') {
            showError('email-error', 'Email is required.');
            isValid = false;
        }

        // Password validation
        const password = document.querySelector('#password');
        if (password.value.trim() === '') {
            showError('password-error', 'Password is required.');
            isValid = false;
        }

        return isValid;
    }

    function showError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }

    // Set active link in navigation
    const currentPage = window.location.pathname.split('/').pop();
    if (currentPage === '') {
        document.querySelector('.nav-link[href="index.html"]').classList.add('active');
    } else {
        const activeLink = document.querySelector(`.nav-link[href="${currentPage}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
    }
    
    // Set active link in dashboard navigation
    const dashboardLinks = document.querySelectorAll('.dashboard-nav a');
    dashboardLinks.forEach(link => {
        if (link.getAttribute('href') === currentPage) {
            link.classList.add('active');
        }
    });

});
