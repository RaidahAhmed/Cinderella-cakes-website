import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import PublicLayout from './components/PublicLayout';
import Home from './pages/Home';
import About from './pages/About';
import Gallery from './pages/Gallery';
import CakeDetail from './pages/CakeDetail';
import Order from './pages/Order';
import Contact from './pages/Contact';

// Admin imports — lazy loaded so they don't bloat the initial public page bundle
const AdminLayout = lazy(() => import('./components/admin/AdminLayout'));
const Dashboard = lazy(() => import('./pages/admin/Dashboard'));
const Login = lazy(() => import('./pages/admin/Login'));
const AdminOrders = lazy(() => import('./pages/admin/Orders'));
const AdminGallery = lazy(() => import('./pages/admin/Gallery'));
const AdminSettings = lazy(() => import('./pages/admin/Settings'));
const ContentEditor = lazy(() => import('./pages/admin/ContentEditor'));
const AdminReviews = lazy(() => import('./pages/admin/Reviews'));
const AdminBlog = lazy(() => import('./pages/admin/Blog'));

// Public secondary pages are lazy loaded too so they stay out of the home bundle.
const Track = lazy(() => import('./pages/Track'));
const Reviews = lazy(() => import('./pages/Reviews'));
const Blog = lazy(() => import('./pages/Blog'));
const BlogPost = lazy(() => import('./pages/BlogPost'));

function AdminFallback() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', fontFamily: 'var(--font-body)', color: 'var(--purple-dark)' }}>
      Loading...
    </div>
  );
}

function PageFallback() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', fontFamily: 'var(--font-body)', color: 'var(--purple-dark)' }}>
      Loading...
    </div>
  );
}

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
          <Route path="/gallery/:id" element={<CakeDetail />} />
          <Route path="/blog" element={
            <Suspense fallback={<PageFallback />}>
              <Blog />
            </Suspense>
          } />
          <Route path="/blog/:slug" element={
            <Suspense fallback={<PageFallback />}>
              <BlogPost />
            </Suspense>
          } />
          <Route path="/order" element={<Order />} />
          <Route path="/track" element={
            <Suspense fallback={<PageFallback />}>
              <Track />
            </Suspense>
          } />
          <Route path="/reviews" element={
            <Suspense fallback={<PageFallback />}>
              <Reviews />
            </Suspense>
          } />
          <Route path="/contact" element={<Contact />} />
        </Route>
        
        {/* Admin Pages — lazy loaded, no Header/Footer */}
        <Route path="/admin/login" element={
          <Suspense fallback={<AdminFallback />}>
            <Login />
          </Suspense>
        } />
        <Route path="/admin" element={
          <Suspense fallback={<AdminFallback />}>
            <AdminLayout />
          </Suspense>
        }>
          {/* The Dashboard loads inside the AdminLayout wrapper when visiting /admin */}
          <Route index element={<Dashboard />} />
          <Route path="orders" element={<AdminOrders />} />
          <Route path="gallery" element={<AdminGallery />} />
          <Route path="reviews" element={<AdminReviews />} />
          <Route path="blog" element={<AdminBlog />} />
          <Route path="content" element={<ContentEditor />} />
          <Route path="settings" element={<AdminSettings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
