import { Outlet, Navigate } from 'react-router-dom';
import AdminSidebar from './AdminSidebar';
import '../../styles/admin.css';

export default function AdminLayout() {
  const token = localStorage.getItem('token');
  
  if (!token) {
    return <Navigate to="/admin/login" replace />;
  }

  return (
    <div className="admin-layout">
      <AdminSidebar />
      <main className="admin-content">
        <Outlet />
      </main>
    </div>
  );
}
