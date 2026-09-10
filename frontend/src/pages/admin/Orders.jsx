import { useEffect, useState } from 'react';
import { fetchOrders, updateOrderStatus, BASE_URL } from '../../lib/api';
import '../../styles/admin.css';

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const data = await fetchOrders();
      if (data.orders) {
        setOrders(data.orders);
      }
    } catch (err) {
      setError('Failed to load orders.');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (orderId, newStatus) => {
    try {
      await updateOrderStatus(orderId, newStatus);
      // Optimistically update local state
      setOrders(orders.map(order => 
        order.id === orderId ? { ...order, status: newStatus } : order
      ));
    } catch (err) {
      alert('Failed to update order status');
    }
  };

  if (loading) return <div>Loading orders...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Order Management</h1>
      </div>

      <div className="admin-card">
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Customer</th>
                <th>Event Date</th>
                <th>Event Type</th>
                <th>Cake Size</th>
                <th>Delivery</th>
                <th>Status</th>
                <th>Inspiration</th>
              </tr>
            </thead>
            <tbody>
              {orders.map(order => (
                <tr key={order.id}>
                  <td>#{order.id}</td>
                  <td>
                    <strong>{order.full_name}</strong>
                    <br/>
                    <small>{order.phone_number}</small>
                  </td>
                  <td>{new Date(order.event_date).toLocaleDateString()}</td>
                  <td>{order.event_type}</td>
                  <td>{order.cake_size}</td>
                  <td>
                    {order.delivery_type}
                    {order.delivery_address && (
                      <div style={{fontSize: '0.8rem', color: '#666', marginTop: '4px'}}>
                        {order.delivery_address}
                      </div>
                    )}
                  </td>
                  <td>
                    <select 
                      value={order.status}
                      onChange={(e) => handleStatusChange(order.id, e.target.value)}
                      className={`status-select status-${order.status}`}
                    >
                      <option value="pending">Pending</option>
                      <option value="confirmed">Confirmed</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Completed</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  </td>
                  <td>
                    {order.inspiration_image ? (
                      <a href={`${BASE_URL}/static/uploads/inspiration/${order.inspiration_image}`} target="_blank" rel="noopener noreferrer">
                        View Image
                      </a>
                    ) : (
                      <span style={{ color: '#999' }}>None</span>
                    )}
                  </td>
                </tr>
              ))}
              {orders.length === 0 && (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center' }}>No orders found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
