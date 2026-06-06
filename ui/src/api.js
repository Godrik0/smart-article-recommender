const API_BASE = '/api/v1';

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  let response;

  try {
    response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError('Service temporarily unavailable', 0);
  }

  if (response.ok) {
    return response.json();
  }

  let detail;
  try {
    const body = await response.json();
    detail = body.detail;
  } catch {
    detail = null;
  }

  if (response.status === 503 || response.status === 0) {
    throw new ApiError('Service temporarily unavailable', response.status);
  }

  throw new ApiError(detail || 'Request failed', response.status);
}

export async function recommend(payload) {
  return request('/recommend', { method: 'POST', body: JSON.stringify(payload) });
}

export async function fetchRecommendation(id) {
  return request(`/recommend/${id}`);
}

export async function listRecommendations(limit = 20) {
  return request(`/recommend?limit=${limit}`);
}

export async function listArticles(category) {
  const params = category ? `?category=${encodeURIComponent(category)}` : '';
  return request(`/articles${params}`);
}
