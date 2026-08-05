import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import Home from './pages/Home';
import About from './pages/About';
import Gallery from './pages/Gallery';
import Order from './pages/Order';
import Contact from './pages/Contact';

// Admin imports
import AdminLayout from './components/admin/AdminLayout';
import Dashboard from './pages/admin/Dashboard';
import Login from './pages/admin/Login';

// Sets up the main structure and routing for the entire website.
export default function App() {
  return (
    <BrowserRouter>
      {/* The Header is shown on all public pages */}
      <Header />
      <main>
        {/* Connects specific web addresses to their corresponding page components */}
        <Routes>
          {/* Public Pages */}
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/gallery" element={<Gallery />} />
          <Route path="/order" element={<Order />} />
          <Route path="/contact" element={<Contact />} />
          
          {/* Admin Pages */}
          <Route path="/admin/login" element={<Login />} />
          <Route path="/admin" element={<AdminLayout />}>
            {/* The Dashboard loads inside the AdminLayout wrapper when visiting /admin */}
            <Route index element={<Dashboard />} />
            {/* Add more admin routes here as they are built (e.g. Orders, Settings) */}
          </Route>
        </Routes>
      </main>
      {/* The Footer is shown on all public pages */}
      <Footer />
    </BrowserRouter>
  );
}
