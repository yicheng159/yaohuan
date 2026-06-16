// API Base URL - use environment variable or default to relative path
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const apiFetch = (url, options = {}) => {
  const token = localStorage.getItem('token');

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Build full URL
  let fullUrl;
  if (url.startsWith('http://') || url.startsWith('https://')) {
    fullUrl = url;
  } else if (API_BASE_URL.startsWith('http')) {
    // Production: API is on a different domain
    fullUrl = `${API_BASE_URL}${url.startsWith('/') ? url : '/' + url}`;
  } else {
    // Development: API is on the same domain
    fullUrl = url.startsWith('/') ? url : `${API_BASE_URL}/${url}`;
  }

  return fetch(fullUrl, {
    ...options,
    headers
  });
};

export default apiFetch;