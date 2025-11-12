export function saveToken(token) {
  localStorage.setItem("ai_token", token);
}

export function getToken() {
  return localStorage.getItem("ai_token");
}

export function clearToken() {
  localStorage.removeItem("ai_token");
}
