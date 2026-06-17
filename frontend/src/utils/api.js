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

  let apiPath = url;
  if (apiPath.startsWith('/api/')) {
    apiPath = apiPath.slice(4);
  } else if (apiPath.startsWith('/')) {
    apiPath = apiPath.slice(1);
  }

  let fullUrl;
  if (API_BASE_URL.startsWith('http')) {
    const baseUrl = API_BASE_URL.replace(/\/$/, '');
    fullUrl = `${baseUrl}/${apiPath}`;
  } else {
    fullUrl = `/${apiPath}`;
  }

  fullUrl = fullUrl.replace(/\/+/g, '/');

  return fetch(fullUrl, {
    ...options,
    headers
  });
};

export default apiFetch;