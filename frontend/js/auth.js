import { apiRequest } from "./api.js";
import { getCurrentUser, setButtonLoading, setToken, showToast } from "./common.js";

async function redirectAuthenticatedUser() {
    try {
        const user = await getCurrentUser();
        if (user) window.location.replace(user.role === "admin" ? "admin.html" : "jobs.html");
    } catch { /* The form remains available when an old token is invalid. */ }
}

const loginForm = document.querySelector("#login-form");
if (loginForm) {
    redirectAuthenticatedUser();
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const button = loginForm.querySelector("button[type='submit']");
        const error = loginForm.querySelector(".form-error");
        error.textContent = "";
        setButtonLoading(button, true, "Signing in...");
        const formData = new URLSearchParams();
        formData.set("username", loginForm.email.value.trim().toLowerCase());
        formData.set("password", loginForm.password.value);
        try {
            const token = await apiRequest("/auth/login", { method: "POST", body: formData, form: true, auth: false });
            setToken(token.access_token);
            const user = await getCurrentUser({ force: true });
            window.location.replace(user.role === "admin" ? "admin.html" : "jobs.html");
        } catch (apiError) {
            error.textContent = apiError.message;
        } finally { setButtonLoading(button, false); }
    });
}

const registerForm = document.querySelector("#register-form");
if (registerForm) {
    redirectAuthenticatedUser();
    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const button = registerForm.querySelector("button[type='submit']");
        const error = registerForm.querySelector(".form-error");
        error.textContent = "";
        if (registerForm.password.value !== registerForm.confirm_password.value) {
            error.textContent = "Passwords do not match.";
            return;
        }
        setButtonLoading(button, true, "Creating account...");
        try {
            await apiRequest("/auth/register", {
                method: "POST",
                auth: false,
                body: {
                    full_name: registerForm.full_name.value.trim(),
                    email: registerForm.email.value.trim().toLowerCase(),
                    password: registerForm.password.value,
                },
            });
            sessionStorage.setItem("mini_job_notice", "Account created. Sign in to continue.");
            window.location.replace("login.html");
        } catch (apiError) { error.textContent = apiError.message; }
        finally { setButtonLoading(button, false); }
    });
}

const notice = sessionStorage.getItem("mini_job_notice");
if (notice) {
    sessionStorage.removeItem("mini_job_notice");
    showToast(notice, "success");
}
