import { useEffect, useState } from 'react';
import { fetchOrders } from '../../lib/api';

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
          pending: data.orders.filter(o => o.status === 'pending').length,
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
          <h3 style={{ margin: '0 0 8px 0', color: 'var(--ink-soft)' }}>Pending Orders</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--teal)' }}>{stats.pending}</div>
        </div>
      </div>

      <div className="admin-card">
        <h3>Recent Orders</h3>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Customer</th>
                <th>Event Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.slice(0, 5).map(order => (
                <tr key={order.id}>
                  <td>#{order.id}</td>
                  <td>{order.full_name}</td>
                  <td>{new Date(order.event_date).toLocaleDateString()}</td>
                  <td>
                    <span className={`status-badge status-${order.status}`}>{order.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
