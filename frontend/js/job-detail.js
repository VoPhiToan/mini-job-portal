import { apiRequest } from "./api.js";
import { escapeHtml, formatDate, formatSalary, getCurrentUser, isAuthenticated, setButtonLoading, showToast } from "./common.js";

const content = document.querySelector("#job-detail-content");
const jobId = Number(new URLSearchParams(location.search).get("id"));
let job = null;

async function loadDetail() {
    if (!Number.isInteger(jobId) || jobId <= 0) {
        content.innerHTML = '<div class="error-state">Invalid job ID.</div>';
        return;
    }
    try {
        job = await apiRequest(`/jobs/${jobId}`, { auth: false });
        let user = null;
        try { user = await getCurrentUser(); } catch { user = null; }
        const action = !isAuthenticated()
            ? '<a class="btn btn-primary" href="login.html">Login to apply</a><p>Create an account or sign in before applying.</p>'
            : user?.role === "candidate"
                ? '<button class="btn btn-primary" id="apply-button">Apply now</button><p>Your application will start with pending status.</p>'
                : '<p class="status status-pending">Admin account</p><p>Administrators cannot apply to jobs.</p>';
        content.innerHTML = `<div class="detail-layout">
            <article class="card detail-main"><span class="tag">${escapeHtml(job.category_name)}</span><h1>${escapeHtml(job.title)}</h1><p class="detail-company">${escapeHtml(job.company)}</p><div class="detail-meta"><span>⌖ ${escapeHtml(job.location)}</span><span>Salary: ${formatSalary(job.salary_min, job.salary_max)}</span><span>Posted ${formatDate(job.created_at)}</span></div><h2>About this opportunity</h2><p class="job-description">${escapeHtml(job.description)}</p></article>
            <aside class="card apply-card"><h2>Interested in this role?</h2>${action}<a class="text-link" href="jobs.html">← Back to all jobs</a></aside>
        </div>`;
        document.querySelector("#apply-button")?.addEventListener("click", applyToJob);
    } catch (error) { content.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`; }
}

async function applyToJob() {
    const button = document.querySelector("#apply-button");
    setButtonLoading(button, true, "Applying...");
    try {
        await apiRequest(`/jobs/${jobId}/apply`, { method: "POST", body: {} });
        showToast("Application submitted successfully.", "success");
        button.textContent = "Applied";
        button.disabled = true;
    } catch (error) {
        showToast(error.status === 409 ? "You have already applied to this job." : error.message, error.status === 409 ? "warning" : "error");
        setButtonLoading(button, false);
    }
}

loadDetail();
