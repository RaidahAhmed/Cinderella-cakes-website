import { Link } from 'react-router-dom';
import heroImg from '../assets/images/wedding.png';
import storefrontImg from '../assets/images/storefront.png';

// Displays the main landing page containing the hero section, value propositions, and bakery location.
export default function Home() {
  return (
    <>
      <section className="hero">
        <div className="hero-wrap">
          <div className="hero-copy">
            <h1>
              A cake for every <span className="accent">celebration</span>
            </h1>
            <p>
              Handcrafted with love in the heart of Uganda. From intimate birthdays to grand
              weddings, every cake tells your story.
            </p>
            <div className="hero-actions">
              <Link to="/order" className="btn btn-gradient">
                Order Now
              </Link>
              <Link to="/gallery" className="btn btn-outline">
                View Gallery
              </Link>
            </div>
          </div>
          <div className="hero-image">
            <img src={heroImg} alt="Cinderella Cakes Signature Wedding Cake" className="hero-img" style={{borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-card)'}} />
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-heading">
            <span className="eyebrow">Our Promise</span>
            <h2>Why Choose Us?</h2>
            <p>We blend artistry with flavour to create cakes that are as beautiful as they are delicious.</p>
          </div>

          <div className="feature-grid">
            <div className="feature-card">
              <div className="feature-icon" style={{fontSize: '3rem', padding: '24px 24px 0'}}>🚚</div>
              <div className="feature-card-body">
                <h3>Reliable deliveries</h3>
                <p>
                  Your celebration deserves punctuality. We deliver across Kampala and the
                  surrounding areas on time and in perfect condition.
                </p>
              </div>
            </div>

            <div className="feature-card">
              <div className="feature-icon" style={{fontSize: '3rem', padding: '24px 24px 0'}}>🌾</div>
              <div className="feature-card-body">
                <h3>Fresh Ingredients</h3>
                <p>We only use the finest fresh local ingredients to make pure wholesome bites.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section section-tight">
        <div className="container">
          <div className="visit-grid">
            <div className="visit-image">
              <img src={storefrontImg} alt="Bakery Storefront" style={{borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-card)'}} />
            </div>
            <div className="visit-copy">
              <h2>
                Come visit
                <span className="accent">our bakery</span>
              </h2>
              <p>
                Step into a warm and welcoming space and discuss your custom order with
                passionate bakers here.
              </p>
              <div className="visit-detail">
                <span className="icon">📍</span> Ave Maria Rd, Nsambya
              </div>
              <div className="visit-detail">
                <span className="icon">📞</span> +256 781 470984
              </div>
              <Link to="/contact" className="btn btn-gradient">
                Get Directions
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
