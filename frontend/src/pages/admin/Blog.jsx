import { useEffect, useRef, useState } from 'react';
import {
  fetchAdminBlogPosts,
  saveBlogPost,
  deleteBlogPost,
  resolveMediaUrl,
} from '../../lib/api';
import { formatBlogDate } from '../../lib/blog';
import '../../styles/admin.css';

const CATEGORY_SUGGESTIONS = [
  'Cake notes',
  'Planning tips',
  'Weddings',
  'Ideas',
  'Behind the scenes',
  'Good to know',
];

const EMPTY_FORM = {
  id: null,
  title: '',
  category: 'Cake notes',
  excerpt: '',
  content: '',
  published: true,
  cover_image_url: null,
  removeCover: false,
};

// Admin screen for the blog: write, edit, publish/hide and delete articles.
export default function Blog() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [form, setForm] = useState(null); // null = editor closed
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);
  const coverInputRef = useRef(null);

  useEffect(() => {
    loadPosts();
  }, []);

  // Close the editor with Escape.
  useEffect(() => {
    if (!form) return undefined;
    function handleKeyDown(event) {
      if (event.key === 'Escape') setForm(null);
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [form]);

  async function loadPosts() {
    setLoading(true);
    setError(null);
    try {
      setPosts(await fetchAdminBlogPosts());
    } catch (err) {
      setError(err.message || 'Failed to load articles');
    } finally {
      setLoading(false);
    }
  }

  function openNew() {
    setFormError(null);
    setForm({ ...EMPTY_FORM });
  }

  function openEdit(post) {
    setFormError(null);
    setForm({
      id: post.id,
      title: post.title || '',
      category: post.category || 'Cake notes',
      excerpt: post.excerpt || '',
      content: post.content || '',
      published: Boolean(post.published),
      cover_image_url: post.cover_image_url || null,
      removeCover: false,
    });
  }

  function buildFormData(values, coverFile) {
    const data = new FormData();
    data.append('title', values.title.trim());
    data.append('category', values.category.trim());
    data.append('excerpt', values.excerpt.trim());
    data.append('content', values.content.trim());
    data.append('published', values.published ? 'true' : 'false');
    if (coverFile) data.append('cover', coverFile);
    else if (values.removeCover) data.append('remove_cover', 'true');
    return data;
  }

  async function handleSave(event) {
    event.preventDefault();
    if (!form.title.trim()) {
      setFormError('Please give the article a title.');
      return;
    }
    if (!form.content.trim()) {
      setFormError('Please write something in the article body.');
      return;
    }

    setSaving(true);
    setFormError(null);
    try {
      const coverFile = coverInputRef.current?.files?.[0] || null;
      await saveBlogPost(form.id, buildFormData(form, coverFile));
      setForm(null);
      await loadPosts();
    } catch (err) {
      setFormError(err.message || 'Failed to save the article');
    } finally {
      setSaving(false);
    }
  }

  async function togglePublished(post) {
    try {
      const data = new FormData();
      data.append('published', post.published ? 'false' : 'true');
      await saveBlogPost(post.id, data);
      await loadPosts();
    } catch (err) {
      alert(err.message || 'Failed to update the article');
    }
  }

  async function handleDelete(post) {
    if (!window.confirm(`Delete "${post.title}"? This cannot be undone.`)) return;
    try {
      await deleteBlogPost(post.id);
      setPosts((prev) => prev.filter((item) => item.id !== post.id));
    } catch (err) {
      alert(err.message || 'Failed to delete the article');
    }
  }

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Blog</h1>
        <div className="admin-blog-header-actions">
          <span className="admin-count-pill">{posts.length} articles</span>
          <button type="button" className="admin-btn" onClick={openNew}>
            + New article
          </button>
        </div>
      </div>

      {error && <p className="admin-inline-error">{error}</p>}

      <div className="admin-card">
        {loading && <p>Loading articles...</p>}

        {!loading && posts.length === 0 && !error && (
          <p>No articles yet. Click &ldquo;New article&rdquo; to write your first one.</p>
        )}

        {!loading && posts.length > 0 && (
          <ul className="admin-blog-list">
            {posts.map((post) => (
              <li key={post.id} className="admin-blog-row">
                <div className="admin-blog-thumb">
                  {post.cover_image_url ? (
                    <img src={resolveMediaUrl(post.cover_image_url)} alt="" />
                  ) : (
                    <span aria-hidden="true">No image</span>
                  )}
                </div>

                <div className="admin-blog-info">
                  <div className="admin-blog-badges">
                    <span className="admin-category-badge">{post.category}</span>
                    <span className={`admin-blog-status${post.published ? ' is-live' : ''}`}>
                      {post.published ? 'Published' : 'Draft'}
                    </span>
                  </div>
                  <h4>{post.title}</h4>
                  <p>
                    {formatBlogDate(post.created_at)}
                    {post.excerpt ? ` · ${post.excerpt}` : ''}
                  </p>
                </div>

                <div className="admin-blog-actions">
                  <button type="button" className="admin-btn admin-btn-ghost" onClick={() => openEdit(post)}>
                    Edit
                  </button>
                  <button type="button" className="admin-btn admin-btn-ghost" onClick={() => togglePublished(post)}>
                    {post.published ? 'Hide' : 'Publish'}
                  </button>
                  {post.published && (
                    <a
                      className="admin-btn admin-btn-ghost"
                      href={`/blog/${post.slug}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View
                    </a>
                  )}
                  <button type="button" className="admin-btn btn-danger" onClick={() => handleDelete(post)}>
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {form && (
        <div className="admin-modal" role="presentation" onClick={() => setForm(null)}>
          <div
            className="admin-modal-panel admin-blog-editor"
            role="dialog"
            aria-modal="true"
            aria-labelledby="admin-blog-editor-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="admin-modal-head">
              <h3 id="admin-blog-editor-title">{form.id ? 'Edit article' : 'New article'}</h3>
              <button
                type="button"
                className="admin-modal-close"
                onClick={() => setForm(null)}
                aria-label="Close editor"
              >
                <span aria-hidden="true">&times;</span>
              </button>
            </div>

            <form onSubmit={handleSave} className="admin-modal-form">
              <label className="admin-field-label" htmlFor="blog-title">Title</label>
              <input
                id="blog-title"
                type="text"
                className="admin-input"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="E.g., How far ahead should you order your cake?"
                maxLength={180}
                required
                autoFocus
              />

              <label className="admin-field-label" htmlFor="blog-category">Category</label>
              <input
                id="blog-category"
                type="text"
                list="blog-category-options"
                className="admin-input"
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                maxLength={60}
              />
              <datalist id="blog-category-options">
                {CATEGORY_SUGGESTIONS.map((name) => (
                  <option key={name} value={name} />
                ))}
              </datalist>

              <label className="admin-field-label" htmlFor="blog-excerpt">Short summary (shown on the blog list)</label>
              <textarea
                id="blog-excerpt"
                className="admin-input"
                rows={2}
                value={form.excerpt}
                onChange={(e) => setForm({ ...form, excerpt: e.target.value })}
                placeholder="One or two friendly sentences that make people want to read more."
                maxLength={400}
              />

              <label className="admin-field-label" htmlFor="blog-content">Article</label>
              <textarea
                id="blog-content"
                className="admin-input admin-blog-body"
                rows={14}
                value={form.content}
                onChange={(e) => setForm({ ...form, content: e.target.value })}
                placeholder={'Write your article here.\n\nLeave a blank line between paragraphs.\n\n## Start a line with ## to make a heading'}
                required
              />
              <p className="admin-blog-help">
                Leave a blank line between paragraphs. Start a line with <code>## </code> to make a heading.
              </p>

              <label className="admin-field-label" htmlFor="blog-cover">Cover image (optional)</label>
              {form.cover_image_url && !form.removeCover && (
                <div className="admin-blog-cover-preview">
                  <img src={resolveMediaUrl(form.cover_image_url)} alt="Current cover" />
                  <button
                    type="button"
                    className="admin-btn admin-btn-ghost"
                    onClick={() => setForm({ ...form, removeCover: true })}
                  >
                    Remove cover image
                  </button>
                </div>
              )}
              <input
                id="blog-cover"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                ref={coverInputRef}
                className="admin-input"
                style={{ padding: '8px' }}
              />

              <label className="admin-blog-check">
                <input
                  type="checkbox"
                  checked={form.published}
                  onChange={(e) => setForm({ ...form, published: e.target.checked })}
                />
                <span>Published (untick to save as a draft that visitors cannot see)</span>
              </label>

              {formError && <p className="admin-inline-error">{formError}</p>}

              <div className="admin-modal-actions">
                <button type="button" className="admin-btn admin-btn-ghost" onClick={() => setForm(null)}>
                  Cancel
                </button>
                <button type="submit" className="admin-btn" disabled={saving}>
                  {saving ? 'Saving...' : form.id ? 'Save changes' : 'Save article'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
