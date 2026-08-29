import { API_BASE_URL, STORAGE_KEYS } from "./config.js";

export class ApiError extends Error {
    constructor(message, status = 0, details = null) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.details = details;
    }
}

function errorMessage(payload, status) {
    if (typeof payload?.detail === "string") return payload.detail;
    if (Array.isArray(payload?.detail)) {
        return payload.detail.map((item) => item.msg).join(" ");
    }
    if (status === 401) return "Please sign in to continue.";
    if (status === 403) return "You do not have permission to perform this action.";
    return "Something went wrong. Please try again.";
}

export async function apiRequest(path, options = {}) {
    const { method = "GET", body, form = false, auth = true } = options;
    const headers = new Headers(options.headers || {});
    const token = localStorage.getItem(STORAGE_KEYS.token);

    if (auth && token) headers.set("Authorization", `Bearer ${token}`);
    if (body !== undefined && !form) headers.set("Content-Type", "application/json");

    let response;
    try {
        response = await fetch(`${API_BASE_URL}${path}`, {
            method,
            headers,
            body: body === undefined ? undefined : form ? body : JSON.stringify(body),
        });
    } catch (error) {
        throw new ApiError("Cannot connect to the API. Make sure the backend is running.", 0, error);
    }

    if (response.status === 204) return null;
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

    if (!response.ok) {
        throw new ApiError(errorMessage(payload, response.status), response.status, payload);
    }
    return payload;
}
