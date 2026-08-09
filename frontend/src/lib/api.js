export const API_BASE_URL = 'http://localhost:5000/api/v1';
export const API_PUBLIC_URL = 'http://localhost:5000/api/public';
export const BASE_URL = 'http://localhost:5000';

// Retrieves the saved login token to securely identify the user for protected actions.
function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// ========================
// PUBLIC API
// ========================

// Fetches global site configuration like store name and contact details.
export async function fetchSiteSettings() {
  const res = await fetch(`${API_PUBLIC_URL}/settings`);
  if (!res.ok) return null;
  return res.json();
}

// Retrieves the menu links for the website's top navigation bar.
export async function fetchNavigation() {
  const res = await fetch(`${API_PUBLIC_URL}/navigation`);
  if (!res.ok) return [];
  return res.json();
}

// Retrieves the content and links for the website's bottom footer area.
export async function fetchFooter() {
  const res = await fetch(`${API_PUBLIC_URL}/footer`);
  if (!res.ok) return null;
  return res.json();
}

// Fetches the content for a specific page based on its URL address (slug).
export async function fetchPage(slug) {
  const res = await fetch(`${API_PUBLIC_URL}/pages/${slug}`);
  if (!res.ok) return null;
  return res.json();
}

// Retrieves the images and details for the public photo gallery.
export async function fetchGallery() {
  const res = await fetch(`${API_PUBLIC_URL}/gallery`);
  if (!res.ok) return [];
  return res.json();
}

// ========================
// ORDERS API
// ========================

// Sends a new cake order to the backend, transforming data names to match what the server expects.
export async function submitOrder(orderData) {
  // Map frontend names to the specific names the backend needs
  const mapping = {
    fullName: 'full_name',
    phoneNumber: 'phone_number',
    eventType: 'event_type',
    eventDate: 'event_date',
    flavor: 'flavor',
    cakeSize: 'cake_size',
    inspirationImage: 'inspiration_image',
    specialInstructions: 'special_instructions',
    deliveryType: 'delivery_type',
    deliveryAddress: 'delivery_address'
  };

  const formData = new FormData();
  Object.keys(orderData).forEach(key => {
    if (orderData[key] !== undefined && orderData[key] !== null) {
      const backendKey = mapping[key] || key;
      formData.append(backendKey, orderData[key]);
    }
  });

  const res = await fetch(`${API_BASE_URL}/orders/create`, {
    method: 'POST',
    body: formData,
  });
  const data = await res.json();
  return { ok: res.ok, data };
}

// Retrieves all orders for the admin dashboard. Requires the user to be logged in.
export async function fetchOrders() {
  const res = await fetch(`${API_BASE_URL}/orders`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch orders');
  return res.json();
}

// Updates the progress status of a specific order (e.g., from 'pending' to 'completed').
export async function updateOrderStatus(id, status) {
  const res = await fetch(`${API_BASE_URL}/orders/${id}/status`, {
    method: 'PATCH',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  return res.json();
}

// ========================
// ADMIN API (AUTH)
// ========================

// Checks credentials and logs an admin user into the system.
export async function login(email, password) {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return res.json();
}

// Verifies the current user's session and retrieves their profile details.
export async function getMe() {
  const res = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Not authenticated');
  return res.json();
}

// ========================
// ADMIN API (SETTINGS)
// ========================

// Retrieves site settings for admin editing. Requires login.
export async function fetchAdminSettings() {
  const res = await fetch(`${API_BASE_URL}/settings/`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch settings');
  return res.json();
}

// Updates site settings. Requires login.
export async function updateAdminSettings(settingsData) {
  const res = await fetch(`${API_BASE_URL}/settings/`, {
    method: 'PUT',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(settingsData),
  });
  return res.json();
}

// ========================
// ADMIN API (GALLERY)
// ========================

// Uploads a new image and its details to the photo gallery. Requires login.
export async function uploadGalleryItem(formData) {
  const res = await fetch(`${API_BASE_URL}/gallery/create`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });
  return res.json();
}

// Removes an image from the photo gallery. Requires login.
export async function deleteGalleryItem(id) {
  const res = await fetch(`${API_BASE_URL}/gallery/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  return res.json();
}
