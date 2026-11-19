import { useEffect, useState } from 'react';
import { fetchOrders } from '../../lib/api';

const STATUS_LABELS = {
  new: 'New',
  confirmed: 'Confirmed',
  baking: 'Baking',
  ready: 'Ready',
  out_for_delivery: 'Out for Delivery',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
};

// Admin dashboard showing high-level statistics and recent orders.
export default function Dashboard() {
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState({ total: 0, pending: 0, revenue: 0 });

  useEffect(() => {
    fetchOrders().then(data => {
      if (data.orders) {
        setOrders(data.orders);
        setStats({
          total: data.orders.length,
          // Orders start their life as 'new' before the bakery confirms them.
          pending: data.orders.filter(o => o.status === 'new').length,
          // Add revenue if you add a price field later
        });
      }
    }).catch(console.error);
  }, []);

  return (
    <div>
      <div className="admin-header">
        <h1>Dashboard</h1>
      </div>

      <div className="admin-stats-grid">
        <div className="admin-card">
          <h3 style={{ margin: '0 0 8px 0', color: 'var(--ink-soft)' }}>Total Orders</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--purple-dark)' }}>{stats.total}</div>
        </div>
        
        <div className="admin-card">
          <h3 style={{ margin: '0 0 8px 0', color: 'var(--ink-soft)' }}>New Orders</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--teal)' }}>{stats.pending}</div>
        </div>
      </div>

      <div className="admin-card">
        <h3>Recent Orders</h3>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Customer</th>
                <th>Event Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.slice(0, 5).map(order => (
                <tr key={order.id}>
                  <td>
                    <span className="admin-order-ref">{order.order_reference || `#${order.id}`}</span>
                  </td>
                  <td>{order.full_name}</td>
                  <td>{new Date(order.event_date).toLocaleDateString()}</td>
                  <td>
                    <span className={`status-badge status-${order.status}`}>
                      {STATUS_LABELS[order.status] || order.status}
                    </span>
                  </td>
                </tr>
              ))}
              {orders.length === 0 && (
                <tr>
                  <td colSpan="4" style={{ textAlign: 'center' }}>
                    No orders yet.
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
