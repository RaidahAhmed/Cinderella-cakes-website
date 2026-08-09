import { Link } from 'react-router-dom';
import cupcakeImg from '../assets/c-cakes-images/about-pg-vanilla-buttercream.png';
import slicedCakeImg from '../assets/c-cakes-images/Deliciously Moist Vanilla Cake Recipe Perfect for Every Occasion and Sweet Cravings 1.png';

// Displays the company history, mission, vision, and a call-to-action banner.
export default function About() {
  return (
    <>
      <section className="page-banner">
        <span className="eyebrow">Our Story</span>
        <h1>About Cinderella Cakes</h1>
      </section>

      <section className="section">
        <div className="container about-grid">
          <div className="about-copy">
            <h2>
              Baked with love since <span className="year">2015</span>
            </h2>
            <p>
              Founded in <span className="year">2015</span>, Cinderella Cakes is a bakery dedicated to creating delicious,
              beautifully crafted cakes for every occasion. From birthdays and weddings to
              anniversaries, graduations and corporate events, we take pride in designing cakes
              that are as memorable as the moments they celebrate.
            </p>
            <p>
              Every cake is prepared using quality ingredients and attention to detail, ensuring
              great taste and elegant presentation.
            </p>

            <div className="about-block">
              <h3>Mission</h3>
              <p>
                To create high-quality, beautifully designed cakes that bring joy to every
                celebration while providing exceptional customer service.
              </p>
            </div>

            <div className="about-block">
              <h3>Vision</h3>
              <p>
                To become one of Uganda&rsquo;s most trusted and preferred cake brands, recognized
                for creativity and quality.
              </p>
            </div>
          </div>

          <div className="about-images">
            <img src={cupcakeImg} alt="Vanilla buttercream cupcake being decorated" />
            <img src={slicedCakeImg} alt="Sliced vanilla layer cake" />
          </div>
        </div>
      </section>

      <section className="section-tight">
        <div className="container">
          <div className="cta-banner">
            <h2>Ready to create your perfect cake?</h2>
            <Link to="/order" className="btn btn-white">
              Order Your Cake
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
