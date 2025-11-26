export class APIError extends Error {
  constructor(status, code, message) {
    super(message || "API error");
    this.status = status;
    this.code = code || "api_error";
  }
}

export function createHttpClient({ baseUrl, getToken, onUnauthorized }) {
  async function request(path, { method = "GET", headers, body } = {}) {
    const token = getToken?.();

    const res = await fetch(`${baseUrl}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(headers || {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    // пустое тело
    const text = await res.text();
    const data = text ? safeJson(text) : null;

    if (res.status === 401) {
      onUnauthorized?.();
    }

    if (!res.ok) {
      // ожидаем формат {code, message}
      const code = data?.code || "request_failed";
      const message = data?.message || res.statusText;
      throw new APIError(res.status, code, message);
    }

    return data;
  }

  return {
    get: (p) => request(p),
    post: (p, body) => request(p, { method: "POST", body }),
  };
}

function safeJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}
