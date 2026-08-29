import { apiRequest } from "./api.js";
import { escapeHtml, formatDate, getCurrentUser, showToast } from "./common.js";

const container = document.querySelector("#applications-list");

async function protectPage() {
    try {
        const user = await getCurrentUser({ force: true });
        if (!user) { location.replace("login.html"); return false; }
        if (user.role !== "candidate") { location.replace("admin.html"); return false; }
        return true;
    } catch { location.replace("login.html"); return false; }
}

function applicationCard(application) {
    return `<article class="card application-card" data-id="${application.id}"><div><span class="status status-${application.status}">${escapeHtml(application.status)}</span><h2>${escapeHtml(application.job.title)}</h2><p>${escapeHtml(application.job.company)} · ${escapeHtml(application.job.location)}</p><small>Applied ${formatDate(application.created_at)}</small></div><div class="actions"><button class="btn btn-ghost btn-small detail-button" type="button">View details</button>${application.status === "pending" ? '<button class="btn btn-danger btn-small withdraw-button" type="button">Withdraw</button>' : ""}</div><div class="application-detail hidden"></div></article>`;
}

async function loadApplications() {
    container.innerHTML = '<div class="loading-state">Loading your applications…</div>';
    try {
        const applications = await apiRequest("/applications/me");
        container.innerHTML = applications.length ? applications.map(applicationCard).join("") : '<div class="empty-state"><strong>No applications yet.</strong><br><a class="text-link" href="jobs.html">Explore current jobs →</a></div>';
    } catch (error) { container.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`; }
}

container.addEventListener("click", async (event) => {
    const card = event.target.closest(".application-card");
    if (!card) return;
    const id = card.dataset.id;
    if (event.target.closest(".detail-button")) {
        const detail = card.querySelector(".application-detail");
        if (!detail.classList.contains("hidden")) { detail.classList.add("hidden"); return; }
        detail.classList.remove("hidden"); detail.textContent = "Loading details…";
        try { const item = await apiRequest(`/applications/me/${id}`); detail.innerHTML = `<strong>Application #${item.id}</strong><span>Status: ${escapeHtml(item.status)}</span><span>Job: ${escapeHtml(item.job.title)}</span><span>Applied: ${formatDate(item.created_at)}</span>`; }
        catch (error) { detail.textContent = error.message; }
    }
    if (event.target.closest(".withdraw-button")) {
        if (!confirm("Withdraw this pending application?")) return;
        const button = event.target.closest("button"); button.disabled = true;
        try { await apiRequest(`/applications/me/${id}`, { method: "DELETE" }); showToast("Application withdrawn.", "success"); card.remove(); if (!container.children.length) loadApplications(); }
        catch (error) { showToast(error.message, error.status === 409 ? "warning" : "error"); button.disabled = false; }
    }
});

if (await protectPage()) loadApplications();
