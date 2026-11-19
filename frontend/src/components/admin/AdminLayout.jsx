import { Outlet, Navigate } from 'react-router-dom';
import AdminSidebar from './AdminSidebar';
import '../../styles/admin.css';

// Reads the payload of a JWT (base64url encoded) without verifying its signature.
function decodeTokenPayload(token) {
  const payload = token.split('.')[1];
  if (!payload) return null;
  const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
  const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=');
  return JSON.parse(atob(padded));
}

// A stored token is useless once its "exp" claim has passed, so treat it as logged out.
function isTokenExpired(token) {
  try {
    const payload = decodeTokenPayload(token);
    if (!payload || !payload.exp) return false;
    return payload.exp * 1000 <= Date.now();
  } catch {
    // Anything we cannot decode must not be trusted.
    return true;
  }
}

export default function AdminLayout() {
  const token = localStorage.getItem('token');

  if (!token || isTokenExpired(token)) {
    localStorage.removeItem('token');
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
