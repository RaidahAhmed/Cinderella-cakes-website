import { NavLink, useNavigate } from 'react-router-dom';

export default function AdminSidebar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/admin/login');
  };

  return (
    <aside className="admin-sidebar">
      <div className="logo">Cinderella Admin</div>
      <nav className="admin-nav">
        <NavLink to="/admin" end className="admin-nav-link">Dashboard</NavLink>
        <NavLink to="/admin/orders" className="admin-nav-link">Orders</NavLink>
        <NavLink to="/admin/gallery" className="admin-nav-link">Gallery</NavLink>
        <NavLink to="/admin/settings" className="admin-nav-link">Settings</NavLink>
        
        <button 
          onClick={handleLogout} 
          className="admin-nav-link" 
          style={{background: 'none', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left', marginTop: 'auto'}}
        >
          Logout
        </button>
      </nav>
    </aside>
  );
}
