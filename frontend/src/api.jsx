import axios from "axios";
import { getToken } from "./auth"; // Import getToken

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function register(payload) {
    return axios.post(`${API_BASE}/register`, payload);
}

export async function login(email, password) {
    const params = new URLSearchParams();
    params.append("username", email);
    params.append("password", password);
    return axios.post(`${API_BASE}/token`, params);
}

// NEW FUNCTION: Start Interview
export async function startInterview(userId) {
    const token = getToken();
    return axios.post(`${API_BASE}/start_interview`, { user_id: userId }, {
        headers: { Authorization: `Bearer ${token}` }
    });
}

// NEW FUNCTION: Get Questions
export async function getQuestions(level = 1, limit = 5) {
    const token = getToken();
    return axios.get(`${API_BASE}/questions?level=${level}&limit=${limit}`, {
        headers: { Authorization: `Bearer ${token}` }
    });
}