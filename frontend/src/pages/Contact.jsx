import { Link } from 'react-router-dom';
import mapsIcon from '../assets/icons/maps (1).png';
import emailIcon from '../assets/icons/gmail.png';
import phoneIcon from '../assets/icons/phone-call.png';
import fbIcon from '../assets/icons/facebook.png';
import instaIcon from '../assets/icons/instagram.png';

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
              <img src={mapsIcon} alt="Address" className="contact-icon" />
              <div>
                <h4>Ave Maria Rd, Nsambya</h4>
                <p>Available Mon &ndash; Sun</p>
              </div>
            </div>
            <div className="contact-method">
              <img src={emailIcon} alt="Email" className="contact-icon" />
              <div>
                <h4>cinderellacakes@gmail.com</h4>
                <p>Replies within 24 hours</p>
              </div>
            </div>
            <div className="contact-method">
              <img src={phoneIcon} alt="Phone" className="contact-icon" />
              <div>
                <h4>+256781 470984</h4>
                <p>Available Mon &ndash; Sun</p>
              </div>
            </div>
            <div className="contact-method">
              <img src={fbIcon} alt="Facebook" className="contact-icon" />
              <div>
                <h4>Cinderella cakes UG</h4>
                <p>Follow us for daily inspiration</p>
              </div>
            </div>
            <div className="contact-method">
              <img src={instaIcon} alt="Instagram" className="contact-icon" />
              <div>
                <h4>Cinderella Cakes</h4>
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

           <div className="map-card" style={{ marginTop: 32 }}>
            <h3>Find us</h3>
            <iframe
              src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d512.8409969174431!2d32.58435774219951!3d0.29589859725992207!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x177dbd2ea2ee2a3b%3A0x2e71b56c2c046a82!2sCinderella%20Cakes!5e1!3m2!1sen!2sug!4v1786546134240!5m2!1sen!2sug"
              width="600"
              height="450"
              style={{ border: 0, width: '100%', maxWidth: 600 }}
              allowFullScreen=""
              loading="lazy"
              referrerPolicy="strict-origin-when-cross-origin"
              title="Cinderella Cakes location"
            ></iframe>
          </div>

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
