import { BrowserRouter, Routes, Route } from 'react-router-dom';
import PublicLayout from './components/PublicLayout';
import Home from './pages/Home';
import About from './pages/About';
import Gallery from './pages/Gallery';
import Order from './pages/Order';
import Contact from './pages/Contact';

// Admin imports
import AdminLayout from './components/admin/AdminLayout';
import Dashboard from './pages/admin/Dashboard';
import Login from './pages/admin/Login';
import AdminOrders from './pages/admin/Orders';
import AdminGallery from './pages/admin/Gallery';
import AdminSettings from './pages/admin/Settings';

// Sets up the main structure and routing for the entire website.
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Pages wrapped with Header + Footer */}
        <Route element={<PublicLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/gallery" element={<Gallery />} />
          <Route path="/order" element={<Order />} />
          <Route path="/contact" element={<Contact />} />
        </Route>
        
        {/* Admin Pages — no Header/Footer */}
        <Route path="/admin/login" element={<Login />} />
        <Route path="/admin" element={<AdminLayout />}>
          {/* The Dashboard loads inside the AdminLayout wrapper when visiting /admin */}
          <Route index element={<Dashboard />} />
          <Route path="orders" element={<AdminOrders />} />
          <Route path="gallery" element={<AdminGallery />} />
          <Route path="settings" element={<AdminSettings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
