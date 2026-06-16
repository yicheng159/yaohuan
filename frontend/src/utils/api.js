const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const apiFetch = (url, options = {}) => {
  const token = localStorage.getItem('token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const fullUrl = url.startsWith('/') ? url : `${API_BASE_URL}/${url}`;
  
  return fetch(fullUrl, {
    ...options,
    headers
  });
};

export default apiFetch;