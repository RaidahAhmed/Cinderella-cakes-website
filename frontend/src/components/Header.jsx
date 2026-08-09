import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import logoImg from '../assets/logo-no-bg.png';

// The main navigation bar at the top of the website, including a mobile hamburger menu.
export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);

  const linkClass = ({ isActive }) => 'nav-link' + (isActive ? ' active' : '');

  function closeMenu() {
    setMenuOpen(false);
  }

  return (
    <header className="site-header">
      <div className="nav-wrap">
        <NavLink to="/" className="logo" onClick={closeMenu}>
          <img src={logoImg} alt="Cinderella Cakes Logo" />
        </NavLink>

        <button
          className="nav-toggle"
          aria-label="Toggle menu"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        <nav className={'main-nav' + (menuOpen ? ' open' : '')}>
          <NavLink to="/" end className={linkClass} onClick={closeMenu}>
            Home
          </NavLink>
          <NavLink to="/about" className={linkClass} onClick={closeMenu}>
            About
          </NavLink>
          <NavLink to="/gallery" className={linkClass} onClick={closeMenu}>
            Gallery
          </NavLink>
          <NavLink to="/order" className={linkClass} onClick={closeMenu}>
            Order
          </NavLink>
          <NavLink to="/contact" className={linkClass} onClick={closeMenu}>
            Contact
          </NavLink>
          <NavLink to="/order" className="btn btn-gradient nav-cta" onClick={closeMenu}>
            Order Now
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
