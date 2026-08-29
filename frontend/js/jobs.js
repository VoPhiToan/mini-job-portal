import { apiRequest } from "./api.js";
import { escapeHtml, jobCard, showToast } from "./common.js";

const form = document.querySelector("#filters-form");
const list = document.querySelector("#jobs-list");
const count = document.querySelector("#result-count");
const pagination = document.querySelector("#pagination");
const limit = 6;

function currentParams() { return new URLSearchParams(window.location.search); }

async function loadOptions() {
    try {
        const [categories, locations] = await Promise.all([
            apiRequest("/categories", { auth: false }),
            apiRequest("/jobs/meta/locations", { auth: false }),
        ]);
        form.category_id.innerHTML = '<option value="">All categories</option>' + categories.map((item) => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join("");
        form.location.innerHTML = '<option value="">All locations</option>' + locations.map((item) => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("");
        const params = currentParams();
        for (const element of form.elements) if (element.name && params.has(element.name)) element.value = params.get(element.name);
        document.querySelector("#sort").value = params.get("sort") || "newest";
    } catch (error) { showToast(error.message, "error"); }
}

function renderPagination(total, skip) {
    const pages = Math.ceil(total / limit);
    const current = Math.floor(skip / limit) + 1;
    if (pages <= 1) { pagination.innerHTML = ""; return; }
    const buttons = [];
    for (let page = 1; page <= pages; page += 1) {
        if (pages > 7 && Math.abs(page - current) > 2 && page !== 1 && page !== pages) continue;
        buttons.push(`<button data-page="${page}" class="${page === current ? "active" : ""}" aria-label="Page ${page}">${page}</button>`);
    }
    pagination.innerHTML = `<button data-page="${current - 1}" ${current === 1 ? "disabled" : ""}>Previous</button>${buttons.join("")}<button data-page="${current + 1}" ${current === pages ? "disabled" : ""}>Next</button>`;
}

async function loadJobs() {
    list.innerHTML = '<div class="loading-state">Finding opportunities…</div>';
    pagination.innerHTML = "";
    const params = currentParams();
    params.set("limit", String(limit));
    if (!params.has("skip")) params.set("skip", "0");
    try {
        const result = await apiRequest(`/jobs?${params}`, { auth: false });
        count.textContent = `${result.total} job${result.total === 1 ? "" : "s"} found`;
        list.innerHTML = result.items.length ? result.items.map(jobCard).join("") : '<div class="empty-state"><strong>No jobs found.</strong><br>Try adjusting your filters.</div>';
        renderPagination(result.total, result.skip);
    } catch (error) {
        count.textContent = "Unable to load jobs";
        list.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    }
}

form.addEventListener("submit", (event) => {
    event.preventDefault();
    const params = new URLSearchParams();
    new FormData(form).forEach((value, key) => { if (String(value).trim()) params.set(key, String(value).trim()); });
    params.set("sort", document.querySelector("#sort").value);
    history.pushState({}, "", `?${params}`);
    loadJobs();
});
document.querySelector("#reset-filters").addEventListener("click", () => { form.reset(); history.pushState({}, "", "jobs.html"); document.querySelector("#sort").value = "newest"; loadJobs(); });
document.querySelector("#sort").addEventListener("change", (event) => { const params = currentParams(); params.set("sort", event.target.value); params.delete("skip"); history.pushState({}, "", `?${params}`); loadJobs(); });
pagination.addEventListener("click", (event) => { const button = event.target.closest("button[data-page]"); if (!button || button.disabled) return; const params = currentParams(); params.set("skip", String((Number(button.dataset.page) - 1) * limit)); history.pushState({}, "", `?${params}`); loadJobs(); window.scrollTo({ top: 0, behavior: "smooth" }); });
window.addEventListener("popstate", async () => { await loadOptions(); loadJobs(); });

await loadOptions();
loadJobs();
