import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchBlogPosts, resolveMediaUrl } from '../lib/api';
import { formatBlogDate } from '../lib/blog';

// The public "Cake Notes" blog: friendly planning tips from our bakers.
export default function Blog() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [slow, setSlow] = useState(false);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setSlow(false);
    setError(null);

    const slowTimer = setTimeout(() => {
      if (!cancelled) setSlow(true);
    }, 6000);

    fetchBlogPosts()
      .then((data) => {
        if (!cancelled) setPosts(data);
      })
      .catch((err) => {
        if (cancelled) return;
        setPosts([]);
        setError(err.message || 'We could not load the blog right now.');
      })
      .finally(() => {
        clearTimeout(slowTimer);
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      clearTimeout(slowTimer);
    };
  }, [reloadKey]);

  return (
    <>
      <header className="gallery-hero">
        <div className="container gallery-hero-inner">
          <span className="eyebrow">Cake Notes</span>
          <h1 className="gallery-hero-title">Tips, Stories &amp; Cake Planning</h1>
          <p className="gallery-hero-sub">
            Friendly advice from our bakers to help you plan the sweetest celebration.
          </p>
          <span className="gallery-hero-rule" aria-hidden="true" />
        </div>
      </header>

      <section className="section gallery-section">
        <div className="container">
          {loading && (
            <div className="gallery-state" role="status" aria-live="polite">
              <span className="gallery-spinner" aria-hidden="true" />
              <p>{slow ? 'Our kitchen is waking up — the articles are on their way…' : 'Opening the recipe box…'}</p>
            </div>
          )}

          {!loading && error && (
            <div className="gallery-state">
              <p>{error}</p>
              <button type="button" className="btn btn-outline" onClick={() => setReloadKey((key) => key + 1)}>
                Try again
              </button>
            </div>
          )}

          {!loading && !error && posts.length === 0 && (
            <div className="gallery-state">
              <p>Our first cake notes are still in the oven. Please check back soon!</p>
            </div>
          )}

          {!loading && !error && posts.length > 0 && (
            <div className="blog-grid">
              {posts.map((post) => (
                <article key={post.id} className="blog-card">
                  <Link to={`/blog/${post.slug}`} className="blog-card-media" aria-label={`Read ${post.title}`}>
                    {post.cover_image_url ? (
                      <img src={resolveMediaUrl(post.cover_image_url)} alt="" loading="lazy" />
                    ) : (
                      <span className="blog-card-placeholder" aria-hidden="true">
                        {post.category}
                      </span>
                    )}
                  </Link>
                  <div className="blog-card-body">
                    <span className="cake-card-cat">{post.category}</span>
                    <h2 className="blog-card-title">
                      <Link to={`/blog/${post.slug}`}>{post.title}</Link>
                    </h2>
                    {post.excerpt && <p className="blog-card-excerpt">{post.excerpt}</p>}
                    <div className="blog-card-foot">
                      <span className="blog-card-date">{formatBlogDate(post.created_at)}</span>
                      <Link to={`/blog/${post.slug}`} className="cake-card-cta">
                        Read more
                        <span aria-hidden="true">&rarr;</span>
                      </Link>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
