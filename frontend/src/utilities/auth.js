import axios from 'axios';

// Track user activity
let lastActivityTime = Date.now();
let tokenRefreshInterval = null;

// Function to update activity timestamp
export const updateActivity = () => {
  lastActivityTime = Date.now();
};

// Modify this function to always return false
const isInactive = () => {
  return false; // Never consider the user inactive
};

// Setup activity listeners
export const setupActivityTracking = () => {
  // Track various user activities
  const events = ['mousedown', 'keypress', 'scroll', 'touchstart'];
  events.forEach(event => {
    window.addEventListener(event, updateActivity);
  });

  // Setup token refresh interval (keeping token refreshes but without logout)
  tokenRefreshInterval = setInterval(async () => {
    if (isAuthenticated()) {
      try {
        await refreshToken();
      } catch (error) {
        console.error('Token refresh failed:', error);
      }
    }
  }, 7 * 24 * 60 * 60 * 1000); // Refresh token every 7 days
};

// Clean up activity tracking
export const cleanupActivityTracking = () => {
  const events = ['mousedown', 'keypress', 'scroll', 'touchstart'];
  events.forEach(event => {
    window.removeEventListener(event, updateActivity);
  });
  
  if (tokenRefreshInterval) {
    clearInterval(tokenRefreshInterval);
  }
};

// Store tokens in localStorage
export const setTokens = (accessToken, refreshToken) => {
  localStorage.setItem('accessToken', accessToken);
  if (refreshToken) {
    localStorage.setItem('refreshToken', refreshToken);
  }
  updateActivity();
};

// Get access token
export const getAccessToken = () => {
  return localStorage.getItem('accessToken');
};

// Get refresh token
export const getRefreshToken = () => {
  return localStorage.getItem('refreshToken');
};

// Check if user is authenticated
export const isAuthenticated = () => {
  return !!getAccessToken();
};

// Refresh the access token
export const refreshToken = async () => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  try {
    const response = await axios.post('/api/refresh', {}, {
      headers: {
        'Authorization': `Bearer ${refreshToken}`
      }
    });
    
    setTokens(response.data.access_token);
    return response.data.access_token;
  } catch (error) {
    console.error('Error refreshing token:', error);
    logout();
    throw error;
  }
};

// Logout function
export const logout = () => {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  cleanupActivityTracking();
  // Redirect to login page
  window.location.href = '/login';
};
