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
    fullUrl = `${API_BASE_URL}/${apiPath}`;
  } else {
    fullUrl = `/${apiPath}`;
  }

  console.log('apiFetch debug:', { url, apiPath, fullUrl, API_BASE_URL });

  return fetch(fullUrl, {
    ...options,
    headers
  }).then(response => {
    console.log('apiFetch response:', { status: response.status, url: response.url, type: response.type });
    return response;
  });
};

export default apiFetch;