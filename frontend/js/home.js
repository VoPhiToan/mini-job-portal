import { apiRequest } from "./api.js";
import { jobCard } from "./common.js";

const form = document.querySelector("#hero-search-form");
form?.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const params = new URLSearchParams();
    for (const [key, value] of data.entries()) {
        if (String(value).trim()) params.set(key, String(value).trim());
    }
    window.location.href = `jobs.html?${params.toString()}`;
});

async function loadRecentJobs() {
    const container = document.querySelector("#recent-jobs");
    try {
        const result = await apiRequest("/jobs?sort=newest&limit=3", { auth: false });
        container.innerHTML = result.items.length
            ? result.items.map(jobCard).join("")
            : '<div class="empty-state">No jobs are available yet.</div>';
    } catch (error) {
        container.innerHTML = `<div class="error-state">${error.message}</div>`;
    }
}

loadRecentJobs();
