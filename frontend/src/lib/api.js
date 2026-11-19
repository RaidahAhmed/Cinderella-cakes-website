// Configurable API origin. Set VITE_API_URL in a .env file (for example
// VITE_API_URL=http://localhost:5000 or your deployed backend URL).
// When it is left empty the app talks to the same origin that served it.
const API_BASE = (import.meta.env.VITE_API_URL || '').trim().replace(/\/+$/, '');

// Origin used to build absolute links to uploaded media (images live outside /api).
export const BASE_URL = API_BASE;

export function resolveMediaUrl(value) {
  if (!value) return '';
  if (/^(https?:)?\/\//i.test(value)) return value;
  const path = value.replace(/\\/g, '/').replace(/^\/+/, '');
  const local = path.startsWith('static/') ? `/${path}`
    : path.startsWith('gallery/') ? `/static/uploads/${path}`
      : `/static/uploads/inspiration/${path}`;
  return `${BASE_URL}${local}`;
}

export function isVideoMedia(item) {
  return item?.media_type === 'video' || /\.mp4(?:[?#]|$)/i.test(item?.image_url || '');
}

const API_URL = `${API_BASE}/api/v1`;
const PUBLIC_URL = `${API_BASE}/api/public`;
const CONTENT_URL = `${API_BASE}/api`;

// Retrieves the saved login token to securely identify the user for protected actions.
function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Builds an Error carrying the server's own message so callers can surface it.
async function buildError(res, fallbackMessage) {
  const error = new Error(fallbackMessage);
  error.status = res.status;
  try {
    const data = await res.json();
    error.data = data;
    error.errors = data.errors;
    error.message = data.message || data.error || fallbackMessage;
  } catch {
    // Response body was empty or not JSON - keep the fallback message.
  }
  return error;
}

// ========================
// PUBLIC API
// ========================

// Normalises the different gallery payloads the API can return into a plain list.
function normaliseGalleryItems(payload) {
  if (Array.isArray(payload)) return payload;
  if (!payload) return [];
  return payload.items || payload.gallery_items || [];
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Public GET with a timeout and a few patient retries. Free hosting plans put the
// server to sleep when nobody is using it, and the first request can take up to a
// minute to be answered; without this the gallery looks "stuck" or broken.
async function fetchPublic(url, { attempts = 4, timeoutMs = 25000 } = {}) {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(url, { signal: controller.signal });
      // A real answer (even a 404) is final. Only server errors are worth another try.
      if (res.status < 500) return res;
      lastError = await buildError(res, 'The server is busy right now.');
    } catch (err) {
      lastError = err.name === 'AbortError'
        ? new Error('The server is taking a while to wake up.')
        : err;
    } finally {
      clearTimeout(timer);
    }
    if (attempt < attempts) await wait(1500 * attempt);
  }
  throw lastError;
}

// Retrieves the images and details for the public photo gallery.
// An optional category key (e.g. 'wedding') narrows the list to that category.
export async function fetchGallery(category) {
  const filter = category && category !== 'all' ? `?category=${encodeURIComponent(category)}` : '';
  const res = await fetchPublic(`${API_URL}/gallery${filter}`);
  if (!res.ok) throw await buildError(res, 'Failed to fetch gallery');
  return normaliseGalleryItems(await res.json());
}

// Retrieves every gallery category with the number of items it holds.
// Resolves to [{ key, label, count }, ...].
export async function fetchGalleryCategories() {
  const res = await fetchPublic(`${API_URL}/gallery/categories`);
  if (!res.ok) throw await buildError(res, 'Failed to fetch categories');
  const data = await res.json();
  return Array.isArray(data) ? data : data.categories || [];
}

// Retrieves one cake with its story, plus similar cakes from the same category.
// Resolves to { item, categoryLabel, related }.
export async function fetchGalleryDetail(id) {
  const value = String(id).trim();
  if (!/^[0-9]{1,10}$/.test(value) || Number(value) < 1 || Number(value) > 2147483647) {
    throw new Error('That cake could not be found.');
  }
  const res = await fetchPublic(`${API_URL}/gallery/${value}`);
  if (res.status === 404) throw new Error('That cake is no longer in our gallery.');
  if (!res.ok) throw await buildError(res, 'We could not load this cake right now.');
  const data = await res.json();
  return {
    item: data.item,
    categoryLabel: data.category_label,
    related: data.related || [],
  };
}

// ========================
// PUBLIC API (BLOG)
// ========================

// Lists published articles, newest first. Optional { limit }.
export async function fetchBlogPosts({ limit } = {}) {
  const query = limit ? `?limit=${encodeURIComponent(limit)}` : '';
  const res = await fetchPublic(`${API_URL}/blog${query}`);
  if (!res.ok) throw await buildError(res, 'We could not load the blog right now.');
  const data = await res.json();
  return data.posts || [];
}

// Retrieves one published article plus a few more to read next.
// Resolves to { post, more }.
export async function fetchBlogPost(slug) {
  const res = await fetchPublic(`${API_URL}/blog/${encodeURIComponent(slug)}`);
  if (res.status === 404) throw new Error('That article could not be found.');
  if (!res.ok) throw await buildError(res, 'We could not load this article right now.');
  const data = await res.json();
  return { post: data.post, more: data.more || [] };
}

// Retrieves a single gallery item by id (the list endpoint is the public source of truth).
export async function fetchGalleryItem(id) {
  const value = String(id).trim();
  const itemId = Number(value);
  if (!/^[0-9]{1,10}$/.test(value) || itemId < 1 || itemId > 2147483647) {
    throw new Error('That gallery design could not be found.');
  }

  const items = await fetchGallery();
  const item = items.find((entry) => entry.id === itemId);
  if (!item) throw new Error('That gallery design is no longer available.');
  return item;
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
    galleryItemId: 'gallery_item_id',
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

  const res = await fetch(`${API_URL}/orders/create`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw await buildError(res, 'Could not submit your order. Please try again.');
  return res.json();
}

// Retrieves all orders for the admin dashboard. Requires the user to be logged in.
export async function fetchOrders() {
  const res = await fetch(`${API_URL}/orders`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw await buildError(res, 'Failed to fetch orders');
  return res.json();
}

// Updates the progress status of a specific order (e.g., from 'new' to 'ready').
export async function updateOrderStatus(id, status) {
  const res = await fetch(`${API_URL}/orders/${id}/status`, {
    method: 'PATCH',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw await buildError(res, 'Failed to update order status');
  return res.json();
}

// ========================
// ADMIN API (AUTH)
// ========================

// Checks credentials and logs an admin user into the system.
export async function login(email, password) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw await buildError(res, 'Login failed');
  return res.json();
}

// Verifies the current user's session and retrieves their profile details.
export async function getMe() {
  const res = await fetch(`${API_URL}/auth/me`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw await buildError(res, 'Not authenticated');
  return res.json();
}

// ========================
// ADMIN API (SETTINGS)
// ========================

// Retrieves site settings for admin editing. Requires login.
export async function fetchAdminSettings() {
  const res = await fetch(`${API_URL}/settings/`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw await buildError(res, 'Failed to fetch settings');
  return res.json();
}

// Updates site settings. Requires login.
export async function updateAdminSettings(settingsData) {
  const res = await fetch(`${API_URL}/settings/`, {
    method: 'PUT',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(settingsData),
  });
  if (!res.ok) throw await buildError(res, 'Failed to update settings');
  return res.json();
}

// ========================
// ADMIN API (GALLERY)
// ========================

// Updates the editable details of a gallery item (title, description, category). Requires login.
export async function updateGalleryItem(id, data) {
  const res = await fetch(`${API_URL}/gallery/${id}`, {
    method: 'PUT',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await buildError(res, 'Failed to update gallery item');
  return res.json();
}

// Uploads a new image and its details to the photo gallery. Requires login.
export async function uploadGalleryItem(formData) {
  const res = await fetch(`${API_URL}/gallery/create`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });
  if (!res.ok) throw await buildError(res, 'Failed to upload image');
  return res.json();
}

// Removes an image from the photo gallery. Requires login.
export async function deleteGalleryItem(id) {
  const res = await fetch(`${API_URL}/gallery/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw await buildError(res, 'Failed to delete image');
  return res.json();
}

// ========================
// ADMIN API (BLOG)
// ========================

// Lists every article, drafts included, with its full text. Requires login.
export async function fetchAdminBlogPosts() {
  const res = await fetch(`${API_URL}/blog/admin/all`, { headers: getAuthHeaders() });
  if (!res.ok) throw await buildError(res, 'Failed to load articles');
  const data = await res.json();
  return data.posts || [];
}

// Creates (no id) or updates (with id) an article. Takes FormData so a cover image can be sent.
export async function saveBlogPost(id, formData) {
  const res = await fetch(`${API_URL}/blog/admin${id ? `/${id}` : ''}`, {
    method: id ? 'PUT' : 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });
  if (!res.ok) throw await buildError(res, 'Failed to save the article');
  return res.json();
}

// Permanently removes an article. Requires login.
export async function deleteBlogPost(id) {
  const res = await fetch(`${API_URL}/blog/admin/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw await buildError(res, 'Failed to delete the article');
  return res.json();
}

// ========================
// ADMIN API (PASSWORD)
// ========================

// Changes the logged-in user's password.
export async function changePassword(currentPassword, newPassword) {
  const res = await fetch(`${API_URL}/auth/change-password`, {
    method: 'POST',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
  if (!res.ok) throw await buildError(res, 'Failed to change password');
  return res.json();
}

// ========================
// ADMIN API (CONTENT EDITING)
// ========================

// Updates a content section's text fields.
export async function updateContentSection(id, data) {
  const res = await fetch(`${CONTENT_URL}/content/sections/${id}`, {
    method: 'PUT',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await buildError(res, 'Failed to update section');
  return res.json();
}

// Updates a content block's text fields.
export async function updateContentBlock(id, data) {
  const res = await fetch(`${CONTENT_URL}/content/blocks/${id}`, {
    method: 'PUT',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await buildError(res, 'Failed to update content block');
  return res.json();
}

// Updates a hero section's text fields.
export async function updateHeroSection(id, data) {
  const res = await fetch(`${CONTENT_URL}/heroes/${id}`, {
    method: 'PUT',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await buildError(res, 'Failed to update hero section');
  return res.json();
}

// Fetches full page data (hero + sections + blocks) for a given slug.
export async function fetchPageBySlug(slug) {
  const res = await fetch(`${PUBLIC_URL}/pages/${slug}`);
  if (!res.ok) throw await buildError(res, 'Failed to load page content');
  return res.json();
}

// ========================
// PUBLIC API (ORDER TRACKING)
// ========================

// Looks up a single order from the public reference plus the phone number
// used when ordering. Returns the order summary and its status timeline.
export async function trackOrder(orderReference, phoneNumber) {
  const res = await fetch(`${API_URL}/track`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ order_reference: orderReference, phone_number: phoneNumber }),
  });
  if (!res.ok) {
    throw await buildError(res, 'We could not find an order with those details. Please try again.');
  }
  return res.json();
}

// ========================
// PUBLIC API (REVIEWS)
// ========================

// Retrieves approved customer reviews together with the rating summary.
export async function fetchReviews() {
  const res = await fetch(`${API_URL}/reviews`);
  if (!res.ok) throw await buildError(res, 'Failed to fetch reviews');
  return res.json();
}

// Sends a new testimonial for moderation. It only appears once approved.
export async function submitReview(data) {
  const res = await fetch(`${API_URL}/reviews`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await buildError(res, 'Could not submit your review. Please try again.');
  return res.json();
}

// ========================
// ADMIN API (REVIEWS)
// ========================

// Lists every review, approved or pending. Requires login.
export async function fetchAdminReviews() {
  const res = await fetch(`${API_URL}/admin/reviews`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw await buildError(res, 'Failed to fetch reviews');
  return res.json();
}

// Toggles a review between approved and pending so it publishes or hides it.
export async function approveReview(id) {
  const res = await fetch(`${API_URL}/admin/reviews/${id}/approve`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw await buildError(res, 'Failed to update review');
  return res.json();
}

// Permanently removes a review. Requires login.
export async function deleteReview(id) {
  const res = await fetch(`${API_URL}/admin/reviews/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw await buildError(res, 'Failed to delete review');
  return res.json();
}
