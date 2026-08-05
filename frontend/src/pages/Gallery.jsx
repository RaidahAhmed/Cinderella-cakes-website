import { Link } from 'react-router-dom';
import Placeholder from '../components/Placeholder';

// Labelled to match what was in your Figma gallery grid - swap each
// Placeholder for an <img src="..." /> of the matching real photo.
const galleryItems = [
  'Panda-themed birthday cake',
  'Spider-Man birthday cake',
  'Cinderella dress cake',
  'Chocolate drip cake with Ferrero Rocher',
  'Chocolate swirl drip cake',
  'White cake with chocolate shards',
  'Pink floral cake',
  'Black glitter "Twenty One" cake',
  'White 3-tier wedding cake',
];

export default function Gallery() {
  return (
    <>
      <section className="page-banner">
        <span className="eyebrow">Our Work</span>
        <h1>Gallery</h1>
        <p>A glimpse into our world of cakes made with passion</p>
      </section>

      <section className="section">
        <div className="container">
          <div className="gallery-grid">
            {galleryItems.map((label) => (
              <Placeholder key={label} label={label} />
            ))}
          </div>

          <div className="gallery-cta">
            <p>Love what you see? Let&rsquo;s create something just for you!</p>
            <Link to="/order" className="btn btn-gradient">
              Order a Custom Cake
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
