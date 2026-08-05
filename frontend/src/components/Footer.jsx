import { Link } from 'react-router-dom';
import logoImg from '../assets/images/logo.png';

// The site-wide footer displaying quick links, contact info, and business hours.
export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-wrap">
        <div className="footer-col footer-brand">
          <img src={logoImg} alt="Cinderella Cakes Logo" style={{height: '50px', objectFit: 'contain', marginBottom: '12px'}} />
          <p>Hand crafted cakes for every celebration in Uganda. Made with love and the finest ingredients.</p>
        </div>

        <div className="footer-col">
          <h4>Quick links</h4>
          <Link to="/">Home</Link>
          <Link to="/about">About</Link>
          <Link to="/gallery">Gallery</Link>
          <Link to="/contact">Contact</Link>
        </div>

        <div className="footer-col">
          <h4>Contact</h4>
          <p>Ave Maria Rd, Nsambya</p>
          <p>+256 781 470984</p>
          <p>cinderellacakes@gmail.com</p>
        </div>

        <div className="footer-col">
          <h4>Hours</h4>
          <p>Mon &ndash; Sat 8am&ndash;7pm</p>
          <p>Sun 9am&ndash;3pm</p>
        </div>
      </div>
      <p className="footer-bottom">&copy; {new Date().getFullYear()} Cinderella Cakes. All rights reserved.</p>
    </footer>
  );
}
