import { Link } from 'react-router-dom';

const hours = [
  ['Monday', '8:00am - 7:00pm'],
  ['Tuesday', '8:00am - 7:00pm'],
  ['Wednesday', '8:00am - 7:00pm'],
  ['Thursday', '8:00am - 7:00pm'],
  ['Friday', '8:00am - 7:00pm'],
  ['Saturday', '8:00am - 7:00pm'],
  ['Sunday', '9:00am - 3:00pm'],
];

// Renders the contact information, business hours, and social media details.
export default function Contact() {
  return (
    <>
      <section className="page-banner">
        <span className="eyebrow">Reach Us</span>
        <h1>Contact Us</h1>
        <p>We&rsquo;d love to hear from you. Find us, call us or drop a message.</p>
      </section>

      <section className="section">
        <div className="container">
          <div className="contact-methods">
            <div className="contact-method">
              <span className="icon">📍</span>
              <div>
                <h4>Ave Maria Rd, Nsambya</h4>
                <p>Available Mon &ndash; Sun</p>
              </div>
            </div>
            <div className="contact-method">
              <span className="icon">✉️</span>
              <div>
                <h4>cinderellacakes@gmail.com</h4>
                <p>Replies within 24 hours</p>
              </div>
            </div>
            <div className="contact-method">
              <span className="icon">📞</span>
              <div>
                <h4>+256 781 470984</h4>
                <p>Available Mon &ndash; Sun</p>
              </div>
            </div>
            <div className="contact-method">
              <span className="icon">📘</span>
              <div>
                <h4>Cinderella Cakes UG</h4>
                <p>Follow us for daily inspiration</p>
              </div>
            </div>
          </div>

          <div className="hours-card">
            <h3>Business hours</h3>
            {hours.map(([day, time]) => (
              <div className="hours-row" key={day}>
                <span>{day}</span>
                <span>{time}</span>
              </div>
            ))}
          </div>

          <div className="ready-card">
            <h2>Ready to order?</h2>
            <p>Fill out an order form and we&rsquo;ll follow up on WhatsApp.</p>
            <Link to="/order" className="btn btn-gradient">
              Place an Order
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
