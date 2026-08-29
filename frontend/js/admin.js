import { apiRequest } from "./api.js";
import { escapeHtml, formatDate, formatSalary, getCurrentUser, setButtonLoading, showToast } from "./common.js";

const guard = document.querySelector("#admin-guard");
const panels = document.querySelectorAll(".admin-panel");
let categories = [];
let jobs = [];

async function protectPage() {
    try {
        const user = await getCurrentUser({ force: true });
        if (!user) { location.replace("login.html"); return false; }
        if (user.role !== "admin") { location.replace("jobs.html"); return false; }
        guard.remove();
        return true;
    } catch { location.replace("login.html"); return false; }
}

document.querySelectorAll(".admin-tab").forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll(".admin-tab").forEach((item) => item.classList.toggle("active", item === button));
    panels.forEach((panel) => panel.classList.toggle("active", panel.id === `panel-${button.dataset.panel}`));
}));

function miniTable(rows) {
    return rows.length ? `<div class="table-wrap"><table class="data-table">${rows.join("")}</table></div>` : '<div class="empty-state">No recent activity.</div>';
}

async function loadDashboard() {
    try {
        const [summary, recentApplications, recentJobs] = await Promise.all([
            apiRequest("/admin/dashboard"), apiRequest("/admin/dashboard/recent-applications?limit=5"), apiRequest("/admin/dashboard/recent-jobs?limit=5"),
        ]);
        const metrics = [
            ["Total users", summary.total_users], ["Candidates", summary.total_candidates], ["Admins", summary.total_admins],
            ["Jobs", summary.total_jobs], ["Categories", summary.total_categories], ["Applications", summary.total_applications],
            ["Pending", summary.pending_applications], ["Accepted", summary.accepted_applications], ["Rejected", summary.rejected_applications],
        ];
        document.querySelector("#stats-grid").innerHTML = metrics.map(([label, value]) => `<article class="stat-card"><span>${label}</span><strong>${value}</strong></article>`).join("");
        document.querySelector("#recent-applications").innerHTML = miniTable(recentApplications.map((item) => `<tr><td><span class="table-title">${escapeHtml(item.candidate_full_name)}</span><span class="table-subtitle">${escapeHtml(item.job_title)}</span></td><td><span class="status status-${item.status}">${item.status}</span></td><td>${formatDate(item.created_at)}</td></tr>`));
        document.querySelector("#recent-jobs-admin").innerHTML = miniTable(recentJobs.map((item) => `<tr><td><span class="table-title">${escapeHtml(item.title)}</span><span class="table-subtitle">${escapeHtml(item.company)}</span></td><td>${escapeHtml(item.location)}</td><td>${formatDate(item.created_at)}</td></tr>`));
    } catch (error) { showToast(error.message, "error"); }
}

async function loadCategories() {
    categories = await apiRequest("/categories", { auth: false });
    document.querySelector("#job-form select[name='category_id']").innerHTML = categories.map((item) => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join("");
}

async function loadJobs() {
    const root = document.querySelector("#admin-jobs");
    root.className = "loading-state"; root.textContent = "Loading jobs…";
    try {
        const result = await apiRequest("/jobs?limit=100&sort=newest", { auth: false });
        jobs = result.items;
        root.className = "table-wrap";
        root.innerHTML = jobs.length ? `<table class="data-table"><thead><tr><th>Job</th><th>Location</th><th>Salary</th><th>Category</th><th>Actions</th></tr></thead><tbody>${jobs.map((job) => `<tr><td><span class="table-title">${escapeHtml(job.title)}</span><span class="table-subtitle">${escapeHtml(job.company)}</span></td><td>${escapeHtml(job.location)}</td><td>${formatSalary(job.salary_min, job.salary_max)}</td><td>${escapeHtml(job.category_name)}</td><td><div class="actions"><button class="btn btn-ghost btn-small edit-job" data-id="${job.id}">Edit</button><button class="btn btn-danger btn-small delete-job" data-id="${job.id}">Delete</button></div></td></tr>`).join("")}</tbody></table>` : '<div class="empty-state">No jobs yet.</div>';
    } catch (error) { root.className = "error-state"; root.textContent = error.message; }
}

function openJobForm(job = null) {
    const form = document.querySelector("#job-form");
    form.classList.remove("hidden");
    form.reset();
    form.job_id.value = job?.id || "";
    document.querySelector("#job-form-title").textContent = job ? "Edit job" : "Create job";
    if (job) for (const field of ["title", "company", "location", "salary_min", "salary_max", "description", "category_id"]) form[field].value = job[field] ?? "";
    form.scrollIntoView({ behavior: "smooth", block: "start" });
}

document.querySelector("#toggle-job-form").addEventListener("click", () => openJobForm());
document.querySelector("#cancel-job-form").addEventListener("click", () => document.querySelector("#job-form").classList.add("hidden"));
document.querySelector("#job-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget; const button = form.querySelector("button[type='submit']"); const error = form.querySelector(".form-error"); error.textContent = "";
    const body = { title: form.title.value.trim(), company: form.company.value.trim(), location: form.location.value.trim(), category_id: Number(form.category_id.value), description: form.description.value.trim(), salary_min: form.salary_min.value ? Number(form.salary_min.value) : null, salary_max: form.salary_max.value ? Number(form.salary_max.value) : null };
    setButtonLoading(button, true, "Saving...");
    try {
        await apiRequest(form.job_id.value ? `/jobs/${form.job_id.value}` : "/jobs", { method: form.job_id.value ? "PUT" : "POST", body });
        showToast(form.job_id.value ? "Job updated successfully." : "Job created successfully.", "success");
        form.classList.add("hidden"); await loadJobs(); await loadDashboard();
    } catch (apiError) { error.textContent = apiError.message; }
    finally { setButtonLoading(button, false); }
});

document.querySelector("#category-form").addEventListener("submit", async (event) => {
    event.preventDefault(); const form = event.currentTarget; const button = form.querySelector("button"); setButtonLoading(button, true, "Adding...");
    try { await apiRequest("/categories", { method: "POST", body: { name: form.name.value.trim() } }); form.reset(); await loadCategories(); showToast("Category created.", "success"); }
    catch (error) { showToast(error.message, error.status === 409 ? "warning" : "error"); }
    finally { setButtonLoading(button, false); }
});

document.querySelector("#admin-jobs").addEventListener("click", async (event) => {
    const id = Number(event.target.closest("button")?.dataset.id); if (!id) return;
    if (event.target.closest(".edit-job")) openJobForm(jobs.find((job) => job.id === id));
    if (event.target.closest(".delete-job")) {
        if (!confirm("Are you sure you want to delete this job?")) return;
        const button = event.target.closest("button"); button.disabled = true;
        try { await apiRequest(`/jobs/${id}`, { method: "DELETE" }); showToast("Job deleted.", "success"); await loadJobs(); await loadDashboard(); }
        catch (error) { showToast(error.message, "error"); button.disabled = false; }
    }
});

async function loadApplications() {
    const root = document.querySelector("#admin-applications"); root.className = "loading-state"; root.textContent = "Loading applications…";
    try {
        const items = await apiRequest("/admin/applications?skip=0&limit=100");
        root.className = "table-wrap";
        root.innerHTML = items.length ? `<table class="data-table"><thead><tr><th>Candidate</th><th>Job</th><th>Applied</th><th>Status</th><th>Detail</th></tr></thead><tbody>${items.map((item) => `<tr><td><span class="table-title">${escapeHtml(item.candidate.full_name)}</span><span class="table-subtitle">${escapeHtml(item.candidate.email)}</span></td><td><span class="table-title">${escapeHtml(item.job.title)}</span><span class="table-subtitle">${escapeHtml(item.job.company)}</span></td><td>${formatDate(item.created_at)}</td><td><select class="status-select" data-id="${item.id}"><option value="pending" ${item.status === "pending" ? "selected" : ""}>Pending</option><option value="accepted" ${item.status === "accepted" ? "selected" : ""}>Accepted</option><option value="rejected" ${item.status === "rejected" ? "selected" : ""}>Rejected</option></select></td><td><button class="btn btn-ghost btn-small view-application" data-id="${item.id}">View</button></td></tr>`).join("")}</tbody></table>` : '<div class="empty-state">No applications yet.</div>';
    } catch (error) { root.className = "error-state"; root.textContent = error.message; }
}

document.querySelector("#admin-applications").addEventListener("change", async (event) => {
    if (!event.target.matches(".status-select")) return;
    event.target.disabled = true;
    try { await apiRequest(`/admin/applications/${event.target.dataset.id}/status`, { method: "PATCH", body: { status: event.target.value } }); showToast("Application status updated.", "success"); await loadDashboard(); }
    catch (error) { showToast(error.message, "error"); await loadApplications(); }
    finally { event.target.disabled = false; }
});
document.querySelector("#admin-applications").addEventListener("click", async (event) => {
    const button = event.target.closest(".view-application"); if (!button) return;
    try { const item = await apiRequest(`/admin/applications/${button.dataset.id}`); showToast(`${item.candidate.full_name} applied for ${item.job.title} — ${item.status}.`, "info"); }
    catch (error) { showToast(error.message, "error"); }
});
document.querySelector("#refresh-dashboard").addEventListener("click", loadDashboard);
document.querySelector("#refresh-applications").addEventListener("click", loadApplications);

if (await protectPage()) {
    await Promise.all([loadCategories(), loadDashboard(), loadApplications()]);
    await loadJobs();
}
