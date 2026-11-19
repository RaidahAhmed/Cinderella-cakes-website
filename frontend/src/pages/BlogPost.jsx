import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { fetchBlogPost, resolveMediaUrl } from '../lib/api';
import { formatBlogDate, parseArticle, readingMinutes } from '../lib/blog';

// A single blog article, with a share button and a few more articles to read next.
export default function BlogPost() {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [slow, setSlow] = useState(false);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [shareNote, setShareNote] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setSlow(false);
    setError(null);
    setShareNote('');
    window.scrollTo({ top: 0 });

    const slowTimer = setTimeout(() => {
      if (!cancelled) setSlow(true);
    }, 6000);

    fetchBlogPost(slug)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (cancelled) return;
        setData(null);
        setError(err.message || 'We could not load this article right now.');
      })
      .finally(() => {
        clearTimeout(slowTimer);
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      clearTimeout(slowTimer);
    };
  }, [slug, reloadKey]);

  const title = data?.post?.title;
  useEffect(() => {
    if (!title) return undefined;
    const previous = document.title;
    document.title = `${title} | Cinderella Cakes`;
    return () => {
      document.title = previous;
    };
  }, [title]);

  if (loading) {
    return (
      <section className="section gallery-section">
        <div className="container">
          <div className="gallery-state" role="status" aria-live="polite">
            <span className="gallery-spinner" aria-hidden="true" />
            <p>{slow ? 'Our kitchen is waking up — one moment…' : 'Opening the article…'}</p>
          </div>
        </div>
      </section>
    );
  }

  if (error || !data?.post) {
    return (
      <section className="section gallery-section">
        <div className="container">
          <div className="gallery-state">
            <p>{error || 'We could not find this article.'}</p>
            <div className="cake-detail-actions">
              <button type="button" className="btn btn-outline" onClick={() => setReloadKey((key) => key + 1)}>
                Try again
              </button>
              <Link to="/blog" className="btn btn-gradient">
                Back to the blog
              </Link>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const { post, more } = data;
  const blocks = parseArticle(post.content);
  const shareUrl = `${window.location.origin}/blog/${post.slug}`;

  async function handleShare() {
    if (navigator.share) {
      try {
        await navigator.share({ title: post.title, url: shareUrl });
        return;
      } catch (err) {
        if (err?.name === 'AbortError') return;
      }
    }
    try {
      await navigator.clipboard.writeText(shareUrl);
      setShareNote('Link copied. Paste it anywhere to share this article.');
    } catch {
      setShareNote(`Copy this link to share: ${shareUrl}`);
    }
  }

  return (
    <section className="section gallery-section">
      <div className="container">
        <article className="blog-article">
          <nav className="cake-detail-crumbs" aria-label="Breadcrumb">
            <Link to="/blog">Cake Notes</Link>
            <span aria-hidden="true">/</span>
            <span>{post.category}</span>
          </nav>

          <h1 className="blog-article-title">{post.title}</h1>
          <p className="blog-article-meta">
            {formatBlogDate(post.created_at)} &middot; {readingMinutes(post.content)} min read
          </p>

          {post.cover_image_url && (
            <img className="blog-article-cover" src={resolveMediaUrl(post.cover_image_url)} alt="" />
          )}

          <div className="blog-article-body">
            {blocks.map((block, index) =>
              block.type === 'h2' ? (
                <h2 key={index}>{block.text}</h2>
              ) : (
                <p key={index}>{block.text}</p>
              ),
            )}
          </div>

          <div className="cake-detail-actions blog-article-actions">
            <Link to="/gallery" className="btn btn-gradient">
              Browse our cakes
            </Link>
            <Link to="/order" className="btn btn-outline">
              Start an order
            </Link>
            <button type="button" className="btn btn-outline" onClick={handleShare}>
              Share this article
            </button>
          </div>
          {shareNote && (
            <p className="cake-detail-note" role="status" aria-live="polite">
              {shareNote}
            </p>
          )}
        </article>

        {more.length > 0 && (
          <div className="cake-related">
            <div className="cake-related-head">
              <h2>More cake notes</h2>
              <Link to="/blog" className="cake-card-cta">
                All articles
                <span aria-hidden="true">&rarr;</span>
              </Link>
            </div>
            <div className="blog-grid">
              {more.map((item) => (
                <article key={item.id} className="blog-card">
                  <div className="blog-card-body">
                    <span className="cake-card-cat">{item.category}</span>
                    <h3 className="blog-card-title">
                      <Link to={`/blog/${item.slug}`}>{item.title}</Link>
                    </h3>
                    {item.excerpt && <p className="blog-card-excerpt">{item.excerpt}</p>}
                    <Link to={`/blog/${item.slug}`} className="cake-card-cta">
                      Read more
                      <span aria-hidden="true">&rarr;</span>
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
