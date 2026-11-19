import { useEffect, useMemo, useState } from 'react';
import { fetchOrders, fetchGallery, updateOrderStatus, resolveMediaUrl } from '../../lib/api';
import GalleryMedia from '../../components/GalleryMedia';
import '../../styles/admin.css';

// Standardised order lifecycle used across the public tracking page and admin.
const STATUS_OPTIONS = [
  { value: 'new', label: 'New' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'baking', label: 'Baking' },
  { value: 'ready', label: 'Ready' },
  { value: 'out_for_delivery', label: 'Out for Delivery' },
  { value: 'delivered', label: 'Delivered' },
  { value: 'cancelled', label: 'Cancelled' },
];

const STATUS_FILTERS = [{ value: 'all', label: 'All statuses' }, ...STATUS_OPTIONS];

function formatDate(value) {
  if (!value) return '—';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? '—' : parsed.toLocaleDateString();
}

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [galleryById, setGalleryById] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [updatingId, setUpdatingId] = useState(null);

  useEffect(() => {
    loadOrders();
  }, []);

  async function loadOrders() {
    setLoading(true);
    setError(null);

    try {
      const data = await fetchOrders();
      setOrders(data.orders || []);
    } catch (err) {
      setError(err.message || 'Failed to load orders.');
    } finally {
      setLoading(false);
    }

    // Design thumbnails come from the gallery list; failures must not hide orders.
    try {
      const items = await fetchGallery();
      setGalleryById(
        items.reduce((map, item) => {
          map[item.id] = item;
          return map;
        }, {}),
      );
    } catch {
      setGalleryById({});
    }
  }

  async function handleStatusChange(orderId, newStatus) {
    setUpdatingId(orderId);
    const previousStatus = orders.find((order) => order.id === orderId)?.status;

    // Optimistically update local state
    setOrders((prev) =>
      prev.map((order) => (order.id === orderId ? { ...order, status: newStatus } : order)),
    );

    try {
      await updateOrderStatus(orderId, newStatus);
    } catch (err) {
      setOrders((prev) =>
        prev.map((order) => (order.id === orderId ? { ...order, status: previousStatus } : order)),
      );
      alert(err.message || 'Failed to update order status');
    } finally {
      setUpdatingId(null);
    }
  }

  // The order list only carries gallery_item_id, so the gallery list fills in
  // the picture and title (the detail endpoint also returns gallery_item).
  function designFor(order) {
    if (order.gallery_item) return order.gallery_item;
    if (order.gallery_item_id) return galleryById[order.gallery_item_id] || null;
    return null;
  }

  const visibleOrders = useMemo(
    () => (statusFilter === 'all' ? orders : orders.filter((order) => order.status === statusFilter)),
    [orders, statusFilter],
  );

  if (loading) return <div>Loading orders...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Order Management</h1>
        <label className="admin-gallery-filter">
          <span>Status</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="admin-input"
          >
            {STATUS_FILTERS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="admin-card">
        <div className="admin-table-wrap">
          <table className="admin-table admin-orders-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Customer</th>
                <th>Event</th>
                <th>Cake</th>
                <th>Delivery</th>
                <th>Design</th>
                <th>Notes</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {visibleOrders.map((order) => {
                const design = designFor(order);

                return (
                  <tr key={order.id}>
                    <td>
                      <span className="admin-order-ref">{order.order_reference || `#${order.id}`}</span>
                      <div className="admin-cell-sub">#{order.id}</div>
                    </td>
                    <td>
                      <strong>{order.full_name}</strong>
                      <div className="admin-cell-sub">{order.phone_number}</div>
                    </td>
                    <td>
                      {formatDate(order.event_date)}
                      <div className="admin-cell-sub">{order.event_type}</div>
                    </td>
                    <td>
                      {order.cake_size || '—'}
                      <div className="admin-cell-sub">{order.flavor || 'No flavor set'}</div>
                    </td>
                    <td>
                      <span className="admin-delivery-tag">{order.delivery_type}</span>
                      {order.delivery_address && (
                        <div className="admin-cell-sub">{order.delivery_address}</div>
                      )}
                    </td>
                    <td>
                      {design ? (
                        <div className="admin-design-cell">
                          <GalleryMedia item={design} className="admin-design-thumb" />
                          <span className="admin-design-title">{design.title || 'Gallery design'}</span>
                        </div>
                      ) : order.inspiration_image ? (
                        <a
                          href={resolveMediaUrl(order.inspiration_image)}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          View upload
                        </a>
                      ) : (
                        <span className="admin-cell-muted">None</span>
                      )}
                    </td>
                    <td>
                      {order.special_instructions ? (
                        <span className="admin-note-cell" title={order.special_instructions}>
                          {order.special_instructions}
                        </span>
                      ) : (
                        <span className="admin-cell-muted">—</span>
                      )}
                    </td>
                    <td>
                      <select
                        value={order.status}
                        onChange={(e) => handleStatusChange(order.id, e.target.value)}
                        className={`status-select status-${order.status}`}
                        disabled={updatingId === order.id}
                        aria-label={`Status for order ${order.order_reference || order.id}`}
                      >
                        {STATUS_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                );
              })}
              {visibleOrders.length === 0 && (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center' }}>
                    No orders found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
