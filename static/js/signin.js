/**
 * AIAS Sign-In System — Frontend Logic
 * Handles form submissions, OTP input, toasts, and password strength.
 */

// ── Toast Notification System ──
class ToastManager {
    constructor() {
        this.container = document.querySelector('.toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    }

    show(message, type = 'info', duration = 5000) {
        const icons = { error: '✕', success: '✓', warning: '⚠', info: 'ℹ' };
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${message}</span>`;
        this.container.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('toast-exit');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

const toast = new ToastManager();

// ── CSRF Token Helper ──
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

// ── Form Submit Helper ──
async function submitForm(url, formData, button) {
    button.classList.add('loading');
    button.disabled = true;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCSRFToken() },
            body: formData,
        });

        const data = await response.json();

        if (data.success) {
            toast.show(data.message, 'success');
            if (data.redirect) {
                setTimeout(() => window.location.href = data.redirect, 800);
            }
        } else {
            toast.show(data.error || 'Something went wrong.', 'error');
        }

        return data;
    } catch (err) {
        toast.show('Network error. Please try again.', 'error');
        return { success: false };
    } finally {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

// ── Sign-In Form ──
function initSigninForm() {
    const form = document.getElementById('signin-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = form.querySelector('.btn-primary');
        const formData = new FormData(form);
        await submitForm(form.action || '/signin', formData, btn);
    });
}

// ── Register Form ──
function initRegisterForm() {
    const form = document.getElementById('register-form');
    if (!form) return;

    const passwordInput = form.querySelector('#password');
    const confirmInput = form.querySelector('#confirm_password');

    if (confirmInput) {
        const markInteracted = () => { confirmInput.dataset.userInteracted = 'true'; };
        confirmInput.addEventListener('focus', markInteracted);
        confirmInput.addEventListener('input', markInteracted);
        confirmInput.addEventListener('change', markInteracted);
        confirmInput.addEventListener('keydown', markInteracted);
        confirmInput.addEventListener('paste', markInteracted);
    }

    if (passwordInput) {
        passwordInput.addEventListener('input', () => {
            updatePasswordStrength(passwordInput.value);
            if (confirmInput && document.activeElement === passwordInput) {
                // If user is typing in password and hasn't interacted with confirm_password,
                // clear confirm_password to prevent automatic mirroring/autofill.
                if (!confirmInput.dataset.userInteracted) {
                    confirmInput.value = '';
                }
            }
        });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const pw = form.querySelector('#password').value;
        const cpw = form.querySelector('#confirm_password').value;
        if (pw !== cpw) { toast.show('Passwords do not match.', 'error'); return; }
        const btn = form.querySelector('.btn-primary');
        await submitForm(form.action || '/register', new FormData(form), btn);
    });
}

// ── Password Strength ──
function updatePasswordStrength(password) {
    const fill = document.querySelector('.strength-fill');
    const text = document.querySelector('.strength-text');
    if (!fill || !text) return;

    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    const levels = ['', 'weak', 'fair', 'good', 'strong'];
    const labels = ['', 'Weak', 'Fair', 'Good', 'Strong'];

    fill.className = 'strength-fill ' + (levels[score] || '');
    text.className = 'strength-text ' + (levels[score] || '');
    text.textContent = labels[score] || '';
}

// ── Password Toggle ──
function initPasswordToggles() {
    document.querySelectorAll('.password-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = btn.parentElement.querySelector('input');
            if (input.type === 'password') {
                input.type = 'text';
                btn.textContent = '🙈';
            } else {
                input.type = 'password';
                btn.textContent = '👁';
            }
        });
    });
}

// ── OTP Input System ──
function initOTPInputs() {
    const inputs = document.querySelectorAll('.otp-input');
    if (!inputs.length) return;

    inputs.forEach((input, index) => {
        input.addEventListener('input', (e) => {
            const val = e.target.value.replace(/\D/g, '');
            e.target.value = val.slice(0, 1);

            if (val && index < inputs.length - 1) {
                inputs[index + 1].focus();
            }

            e.target.classList.toggle('filled', !!val);
            e.target.classList.remove('error');
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && !e.target.value && index > 0) {
                inputs[index - 1].focus();
                inputs[index - 1].value = '';
                inputs[index - 1].classList.remove('filled');
            }
        });

        input.addEventListener('focus', () => input.select());
    });

    // Paste support
    inputs[0]?.addEventListener('paste', (e) => {
        e.preventDefault();
        const pasted = (e.clipboardData.getData('text') || '').replace(/\D/g, '').slice(0, 6);
        pasted.split('').forEach((ch, i) => {
            if (inputs[i]) {
                inputs[i].value = ch;
                inputs[i].classList.add('filled');
            }
        });
        if (pasted.length > 0) inputs[Math.min(pasted.length, inputs.length) - 1].focus();
    });
}

function getOTPValue() {
    return Array.from(document.querySelectorAll('.otp-input')).map(i => i.value).join('');
}

// ── OTP Verification Form ──
function initOTPForm() {
    const form = document.getElementById('otp-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const otp = getOTPValue();
        if (otp.length !== 6) {
            toast.show('Please enter all 6 digits.', 'error');
            document.querySelectorAll('.otp-input').forEach(i => i.classList.add('error'));
            return;
        }

        const formData = new FormData();
        formData.append('otp', otp);

        const btn = form.querySelector('.btn-primary');
        await submitForm(form.action || '/verify-otp', formData, btn);
    });
}

// ── OTP Timer ──
function initOTPTimer(initialSeconds) {
    const timerEl = document.querySelector('.otp-timer .time');
    if (!timerEl) return;

    if (window.otpInterval) clearInterval(window.otpInterval);

    let seconds = initialSeconds;

    window.otpInterval = setInterval(() => {
        seconds--;
        if (seconds <= 0) {
            clearInterval(window.otpInterval);
            timerEl.textContent = 'Expired';
            timerEl.classList.add('expiring');
            toast.show('Verification code expired. Please request a new one.', 'warning');
            return;
        }
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        timerEl.textContent = `${m}:${s.toString().padStart(2, '0')}`;
        if (seconds <= 60) {
            timerEl.classList.add('expiring');
        } else {
            timerEl.classList.remove('expiring');
        }
    }, 1000);
}

// ── Resend OTP ──
function initResendOTP() {
    const btn = document.getElementById('resend-btn');
    if (!btn) return;

    btn.addEventListener('click', async () => {
        btn.disabled = true;
        btn.textContent = 'Sending...';

        try {
            const res = await fetch('/resend-otp', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCSRFToken(), 'Content-Type': 'application/json' },
            });
            const data = await res.json();
            if (data.success) {
                toast.show(data.message, 'success');
                // Reset timer (5 minutes = 300 seconds)
                initOTPTimer(300);
                // Clear inputs
                document.querySelectorAll('.otp-input').forEach(i => { i.value = ''; i.classList.remove('filled', 'error'); });
                document.querySelector('.otp-input')?.focus();

                // Cooldown
                let cd = 30;
                btn.textContent = `Resend in ${cd}s`;
                const cdInterval = setInterval(() => {
                    cd--;
                    btn.textContent = `Resend in ${cd}s`;
                    if (cd <= 0) { clearInterval(cdInterval); btn.disabled = false; btn.textContent = 'Resend Code'; }
                }, 1000);
            } else {
                toast.show(data.error, 'error');
                btn.disabled = false;
                btn.textContent = 'Resend Code';
            }
        } catch {
            toast.show('Failed to resend code.', 'error');
            btn.disabled = false;
            btn.textContent = 'Resend Code';
        }
    });
}

// ── Forgot Password Form ──
function initForgotPasswordForm() {
    const form = document.getElementById('forgot-password-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = form.querySelector('.btn-primary');
        await submitForm(form.action || '/forgot-password', new FormData(form), btn);
    });
}

// ── Reset Password Form ──
function initResetPasswordForm() {
    const form = document.getElementById('reset-password-form');
    if (!form) return;

    // Password strength indicator
    const passwordInput = form.querySelector('#password');
    const confirmInput = form.querySelector('#confirm_password');

    if (confirmInput) {
        const markInteracted = () => { confirmInput.dataset.userInteracted = 'true'; };
        confirmInput.addEventListener('focus', markInteracted);
        confirmInput.addEventListener('input', markInteracted);
        confirmInput.addEventListener('change', markInteracted);
        confirmInput.addEventListener('keydown', markInteracted);
        confirmInput.addEventListener('paste', markInteracted);
    }

    if (passwordInput) {
        passwordInput.addEventListener('input', () => {
            updatePasswordStrength(passwordInput.value);
            if (confirmInput && document.activeElement === passwordInput) {
                // If user is typing in password and hasn't interacted with confirm_password,
                // clear confirm_password to prevent automatic mirroring/autofill.
                if (!confirmInput.dataset.userInteracted) {
                    confirmInput.value = '';
                }
            }
        });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const password = form.querySelector('#password').value;
        const confirmPassword = form.querySelector('#confirm_password').value;

        if (password !== confirmPassword) {
            toast.show('Passwords do not match.', 'error');
            return;
        }
        if (password.length < 8) {
            toast.show('Password must be at least 8 characters.', 'error');
            return;
        }

        const btn = form.querySelector('.btn-primary');
        await submitForm(form.action || '/reset-password', new FormData(form), btn);
    });
}

// ── Initialize Everything ──
document.addEventListener('DOMContentLoaded', () => {
    initSigninForm();
    initRegisterForm();
    initForgotPasswordForm();
    initResetPasswordForm();
    initPasswordToggles();
    initOTPInputs();
    initOTPForm();
    initResendOTP();

    // Flash messages from server
    document.querySelectorAll('.flash-message').forEach(el => {
        toast.show(el.dataset.message, el.dataset.type || 'info');
        el.remove();
    });
});
