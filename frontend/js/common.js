import { apiRequest } from "./api.js";
import { STORAGE_KEYS } from "./config.js";

let currentUserPromise = null;

export function getToken() {
    return localStorage.getItem(STORAGE_KEYS.token);
}

export function setToken(token) {
    localStorage.setItem(STORAGE_KEYS.token, token);
}

export function clearSession() {
    localStorage.removeItem(STORAGE_KEYS.token);
    localStorage.removeItem(STORAGE_KEYS.user);
    currentUserPromise = null;
}

export function isAuthenticated() {
    return Boolean(getToken());
}

export async function getCurrentUser({ force = false } = {}) {
    if (!isAuthenticated()) return null;
    if (!currentUserPromise || force) {
        currentUserPromise = apiRequest("/auth/me").then((user) => {
            localStorage.setItem(STORAGE_KEYS.user, JSON.stringify({
                id: user.id,
                full_name: user.full_name,
                role: user.role,
            }));
            return user;
        }).catch((error) => {
            if (error.status === 401) clearSession();
            throw error;
        });
    }
    return currentUserPromise;
}

export function escapeHtml(value = "") {
    return String(value).replace(/[&<>'"]/g, (character) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
    })[character]);
}

export function formatDate(value) {
    if (!value) return "—";
    return new Intl.DateTimeFormat("en", {
        day: "2-digit", month: "short", year: "numeric",
    }).format(new Date(value));
}

export function formatSalary(minimum, maximum) {
    const number = (value) => new Intl.NumberFormat("en-US").format(value);
    if (minimum == null && maximum == null) return "Negotiable";
    if (minimum != null && maximum != null) return `${number(minimum)} – ${number(maximum)}`;
    if (minimum != null) return `From ${number(minimum)}`;
    return `Up to ${number(maximum)}`;
}

export function showToast(message, type = "info") {
    const root = document.querySelector("#toast-root") || document.body;
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.setAttribute("role", "status");
    toast.textContent = message;
    root.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("is-visible"));
    setTimeout(() => {
        toast.classList.remove("is-visible");
        setTimeout(() => toast.remove(), 250);
    }, 3500);
}

export function setButtonLoading(button, loading, loadingText = "Working...") {
    if (loading) {
        button.dataset.originalText = button.textContent;
        button.textContent = loadingText;
        button.disabled = true;
    } else {
        button.textContent = button.dataset.originalText || button.textContent;
        button.disabled = false;
    }
}

function navbarMarkup(user) {
    const page = document.body.dataset.page;
    const active = (name) => page === name ? 'aria-current="page" class="active"' : "";
    const roleLink = user?.role === "admin"
        ? `<a ${active("admin")} href="admin.html">Admin Dashboard</a>`
        : user ? `<a ${active("applications")} href="applications.html">My Applications</a>` : "";
    const authArea = user
        ? `<span class="nav-user">${escapeHtml(user.full_name)}</span><button class="btn btn-ghost btn-small" id="logout-button">Logout</button>`
        : `<a class="btn btn-ghost btn-small" href="login.html">Login</a><a class="btn btn-primary btn-small" href="register.html">Register</a>`;
    return `<div class="container nav-inner">
        <a class="brand" href="index.html" aria-label="MiniJob home"><span>Mini</span>Job</a>
        <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation" aria-expanded="false">☰</button>
        <nav class="nav-links" id="nav-links" aria-label="Main navigation">
            <a ${active("home")} href="index.html">Home</a>
            <a ${active("jobs")} href="jobs.html">Jobs</a>
            ${roleLink}
            <div class="nav-actions">${authArea}</div>
        </nav>
    </div>`;
}

export async function initializeNavbar() {
    const navbar = document.querySelector("#navbar");
    if (!navbar) return null;
    let user = null;
    try { user = await getCurrentUser(); } catch { user = null; }
    navbar.innerHTML = navbarMarkup(user);
    document.querySelector("#nav-toggle")?.addEventListener("click", () => {
        const links = document.querySelector("#nav-links");
        const open = links.classList.toggle("is-open");
        document.querySelector("#nav-toggle").setAttribute("aria-expanded", String(open));
    });
    document.querySelector("#logout-button")?.addEventListener("click", () => {
        clearSession();
        window.location.href = "index.html";
    });
    return user;
}

export function jobCard(job) {
    return `<article class="job-card">
        <div class="job-card-top"><span class="tag">${escapeHtml(job.category_name)}</span><span class="date">${formatDate(job.created_at)}</span></div>
        <h3><a href="job-detail.html?id=${job.id}">${escapeHtml(job.title)}</a></h3>
        <p class="company">${escapeHtml(job.company)}</p>
        <div class="job-meta"><span>⌖ ${escapeHtml(job.location)}</span><span>Salary: ${formatSalary(job.salary_min, job.salary_max)}</span></div>
        <a class="text-link" href="job-detail.html?id=${job.id}">View details <span aria-hidden="true">→</span></a>
    </article>`;
}

document.addEventListener("DOMContentLoaded", initializeNavbar);
