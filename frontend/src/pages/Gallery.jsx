import { Link } from 'react-router-dom';

const mediaFiles = import.meta.glob('../assets/gallery/*.{png,jpg,jpeg,webp,mp4}', { eager: true });

const galleryItems = Object.keys(mediaFiles).map((key, index) => {
  const isVideo = key.endsWith('.mp4');
  return {
    src: mediaFiles[key].default,
    isVideo,
    alt: 'Cake design',
    id: index + 1,
  };
});

// Shows a grid of previous cake designs to inspire customers.
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
            {galleryItems.map((item) => (
              <div key={item.id} className="gallery-item">
                {item.isVideo ? (
                  <video
                    src={item.src}
                    controls
                    preload="metadata"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                ) : (
                  <img src={item.src} alt={item.alt} loading="lazy" />
                )}
                <div className="gallery-item-overlay">
                  <Link
                    to={`/order?gallery_ref=${item.id}`}
                    className="btn btn-gradient gallery-order-btn"
                  >
                    Order This Cake
                  </Link>
                </div>
              </div>
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
