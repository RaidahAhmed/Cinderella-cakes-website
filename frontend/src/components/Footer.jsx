import { Link, useLocation } from 'react-router-dom';
import logoImg from '../assets/logo-no-bg.png';

// The site-wide footer displaying quick links, contact info, and business hours.
export default function Footer() {
  const { pathname } = useLocation();

  // Highlight the active page link in the footer
  function linkClass(path) {
    const isActive =
      path === '/' ? pathname === '/' : pathname.startsWith(path);
    return isActive ? 'footer-active' : '';
  }

  return (
    <footer className="site-footer">
      <div className="footer-wrap">
        <div className="footer-col footer-brand">
          <div className="footer-brand-header">
            <img src={logoImg} alt="Cinderella Cakes Logo" />
            <span>Cinderella cakes</span>
          </div>
          <p>Hand crafted cakes for every celebration in Uganda. Made with love and the finest ingredients.</p>
        </div>

        <div className="footer-col">
          <h4>Quick links</h4>
          <Link to="/" className={linkClass('/')}>Home</Link>
          <Link to="/about" className={linkClass('/about')}>About</Link>
          <Link to="/gallery" className={linkClass('/gallery')}>Gallery</Link>
          <Link to="/contact" className={linkClass('/contact')}>Contact</Link>
        </div>

        <div className="footer-col">
          <h4>Contact</h4>
          <p>Ave Maria Rd, Nsambya</p>
          <p>+256781 470984</p>
          <p>cinderellacakes@gmail.com</p>
        </div>

        <div className="footer-col">
          <h4>Hours</h4>
          <p>MON - SAT 8am-7pm</p>
          <p>SUN 9am-3pm</p>
        </div>
      </div>
      <p className="footer-bottom">&copy; {new Date().getFullYear()} Cinderella Cakes. All rights reserved.</p>
    </footer>
  );
}
