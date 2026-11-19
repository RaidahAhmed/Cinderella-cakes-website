import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchReviews } from '../lib/api';
import heroImg from '../assets/c-cakes-images/home-pg-hero.png';
import storefrontImg from '../assets/c-cakes-images/visit-bakery.png';
import deliveryImg from '../assets/c-cakes-images/delivery.png';
import ingredientsImg from '../assets/c-cakes-images/fresh-ingridients.png';
import mapsIcon from '../assets/icons/maps (1).png';
import phoneIcon from '../assets/icons/phone-call.png';

// Displays the main landing page containing the hero section, value propositions, and bakery location.
export default function Home() {
  const [testimonials, setTestimonials] = useState([]);

  // Pull the three most recent approved reviews for the testimonial strip.
  useEffect(() => {
    let active = true;

    fetchReviews()
      .then((data) => {
        if (active) setTestimonials((data.reviews || []).slice(0, 3));
      })
      .catch(() => {
        // Testimonials are a nice-to-have, so stay quiet if the API is unreachable.
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <>
      <section className="hero" style={{ backgroundImage: `url(${heroImg})` }}>
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
              <div className="feature-image">
                <img src={deliveryImg} alt="Reliable deliveries" />
              </div>
              <div className="feature-card-body">
                <h3>Reliable deliveries</h3>
                <p>
                  Your celebration deserves punctuality. We deliver across Kampala and the
                  surrounding areas on time and in perfect condition.
                </p>
              </div>
            </div>

            <div className="feature-card">
              <div className="feature-image">
                <img src={ingredientsImg} alt="Fresh Ingredients" />
              </div>
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
              <img src={storefrontImg} alt="Cinderella Cakes Bakery Storefront" />
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
                <img src={mapsIcon} alt="Location" className="visit-icon" />
                Ave Maria Rd, Nsambya
              </div>
              <div className="visit-detail">
                <img src={phoneIcon} alt="Phone" className="visit-icon" />
                +256781 470984
              </div>
              <Link to="/contact" className="btn btn-gradient">
                Get Directions
              </Link>
            </div>
          </div>
        </div>
      </section>

      {testimonials.length > 0 && (
        <section className="section testimonials-section">
          <div className="container">
            <div className="section-heading">
              <span className="eyebrow">Testimonials</span>
              <h2>What Our Customers Say</h2>
              <p>Kind words from the celebrations we have had the joy of baking for.</p>
            </div>

            <div className="testimonial-grid">
              {testimonials.map((review) => (
                <article key={review.id} className="testimonial-card">
                  <span className="review-quote-mark" aria-hidden="true">&ldquo;</span>
                  <Stars value={review.rating} />
                  <p className="testimonial-text">{snippet(review.review_text)}</p>
                  <span className="testimonial-name">{review.customer_name}</span>
                </article>
              ))}
            </div>

            <div className="testimonial-actions">
              <Link to="/reviews" className="btn btn-outline">
                See All Reviews
              </Link>
            </div>
          </div>
        </section>
      )}
    </>
  );
}

// Five star row shared by the testimonial cards.
function Stars({ value }) {
  const filled = Math.round(Number(value) || 0);
  return (
    <span className="stars" aria-label={`${filled} out of 5 stars`}>
      {[1, 2, 3, 4, 5].map((star) => (
        <span key={star} className={`star${star <= filled ? ' filled' : ''}`} aria-hidden="true">
          ★
        </span>
      ))}
    </span>
  );
}

// Trims a review down to a short teaser for the home page cards.
function snippet(text, limit = 180) {
  const value = (text || '').trim();
  if (value.length <= limit) return value;
  return `${value.slice(0, limit).trimEnd()}…`;
}
