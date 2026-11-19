import { useEffect, useRef, useState } from 'react';
import {
  fetchGallery,
  uploadGalleryItem,
  updateGalleryItem,
  deleteGalleryItem,
  isVideoMedia,
} from '../../lib/api';
import GalleryMedia from '../../components/GalleryMedia';
import '../../styles/admin.css';

// Categories accepted by the API (POST /gallery/create and PUT /gallery/<id>).
const CATEGORY_OPTIONS = [
  { value: 'wedding', label: 'Weddings & Introductions' },
  { value: 'birthday', label: 'Birthdays' },
  { value: 'kids', label: "Kids' Characters" },
  { value: 'baby', label: 'Baby Showers' },
  { value: 'graduation', label: 'Graduations' },
  { value: 'anniversary', label: 'Anniversaries & Love' },
  { value: 'corporate', label: 'Corporate & Events' },
  { value: 'holiday', label: 'Holidays & Seasons' },
  { value: 'sculpted', label: 'Sculpted & Sugar Art' },
  { value: 'cupcakes', label: 'Cupcakes & Treats' },
  { value: 'other', label: 'Other' },
];

const CATEGORY_LABELS = Object.fromEntries(
  CATEGORY_OPTIONS.map((option) => [option.value, option.label]),
);

export default function Gallery() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const requestId = useRef(0);
  const filterRef = useRef(filter);
  filterRef.current = filter;
  const gridRef = useRef(null);

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const fileInputRef = useRef(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('other');

  const [editing, setEditing] = useState(null);
  const [savingEdit, setSavingEdit] = useState(false);
  const [editError, setEditError] = useState(null);

  useEffect(() => {
    loadGallery(filter);
    return () => { requestId.current += 1; };
  }, [filter]);

  // Close the edit dialog with Escape.
  useEffect(() => {
    if (!editing) return undefined;

    function handleKeyDown(event) {
      if (event.key === 'Escape') setEditing(null);
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [editing]);

  async function loadGallery(categoryFilter) {
    const currentRequest = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchGallery(categoryFilter === 'all' ? null : categoryFilter);
      if (currentRequest === requestId.current) setItems(Array.isArray(data) ? data : []);
    } catch (err) {
      if (currentRequest === requestId.current) {
        setItems([]);
        setError(err.message || 'Failed to load gallery');
      }
    } finally {
      if (currentRequest === requestId.current) setLoading(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Are you sure you want to delete this image?')) return;

    try {
      await deleteGalleryItem(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      if (editing?.id === id) setEditing(null);
      loadGallery(filterRef.current);
    } catch (err) {
      alert(err.message || 'Failed to delete image');
    }
  }

  async function handleUpload(e) {
    e.preventDefault();
    setUploadError(null);

    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      setUploadError('Please select an image to upload.');
      return;
    }
    if (!title.trim()) {
      setUploadError('A title is required so the design can be found later.');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('image', file);
    formData.append('title', title.trim());
    formData.append('category', category);
    if (description.trim()) formData.append('description', description.trim());

    try {
      const res = await uploadGalleryItem(formData);
      if (res.success) {
        fileInputRef.current.value = '';
        setTitle('');
        setDescription('');
        setCategory('other');
        loadGallery(filterRef.current);
      } else {
        setUploadError(res.message || res.error || 'Upload failed');
      }
    } catch (err) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  function startEditing(item) {
    gridRef.current?.querySelectorAll('video').forEach((video) => video.pause());
    setEditError(null);
    setEditing({
      id: item.id,
      title: item.title || '',
      description: item.description || '',
      category: item.category || 'other',
      image_url: item.image_url,
      media_type: item.media_type,
    });
  }

  async function handleSaveEdit(e) {
    e.preventDefault();
    if (!editing) return;
    if (!editing.title.trim()) {
      setEditError('Title cannot be empty.');
      return;
    }

    setSavingEdit(true);
    setEditError(null);

    try {
      const res = await updateGalleryItem(editing.id, {
        title: editing.title.trim(),
        description: editing.description.trim(),
        category: editing.category,
      });
      const updated = res.item || {
        ...editing,
        title: editing.title.trim(),
        description: editing.description.trim(),
      };

      setItems((prev) => prev.map((item) => (item.id === updated.id ? { ...item, ...updated } : item)));
      setEditing(null);
      loadGallery(filterRef.current);
    } catch (err) {
      setEditError(err.message || 'Failed to save changes');
    } finally {
      setSavingEdit(false);
    }
  }

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Gallery Management</h1>
        <span className="admin-count-pill">{items.length} shown</span>
      </div>

      <div className="admin-card" style={{ marginBottom: '24px' }}>
        <h3>Add a New Cake</h3>
        <form
          onSubmit={handleUpload}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
            alignItems: 'end',
          }}
        >
          <div>
            <label className="admin-field-label">Image File</label>
            <input type="file" accept="image/*" ref={fileInputRef} required className="admin-input" style={{ padding: '8px' }} />
          </div>
          <div>
            <label className="admin-field-label">Title (Required)</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="E.g., Three-tier vanilla rose cake"
              className="admin-input"
              required
            />
          </div>
          <div>
            <label className="admin-field-label">Short story (Optional, shown on the cake's page)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Tell the story: the occasion, the flavours, what makes this cake special..."
              className="admin-input"
              rows={3}
              maxLength={500}
            />
          </div>
          <div>
            <label className="admin-field-label">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="admin-input"
            >
              {CATEGORY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <button type="submit" className="admin-btn" disabled={uploading} style={{ width: '100%', minHeight: '44px' }}>
              {uploading ? 'Uploading...' : 'Upload Image'}
            </button>
          </div>
        </form>
        {uploadError && <p className="admin-inline-error">{uploadError}</p>}
      </div>

      <div className="admin-gallery-toolbar">
        <label className="admin-gallery-filter">
          <span>Filter</span>
          <select value={filter} onChange={(e) => setFilter(e.target.value)} className="admin-input">
            <option value="all">All categories</option>
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && <p className="admin-inline-error">{error}</p>}

      <div className="admin-gallery-grid" ref={gridRef}>
        {loading && <div className="admin-gallery-empty">Loading gallery...</div>}

        {!loading &&
          items.map((item) => (
            <div key={item.id} className="admin-gallery-item">
              {isVideoMedia(item) ? (
                <div className="admin-gallery-thumb">
                  <GalleryMedia item={item} />
                </div>
              ) : (
                <button
                  type="button"
                  className="admin-gallery-thumb"
                  onClick={() => startEditing(item)}
                  title="Edit this image"
                >
                  <GalleryMedia item={item} />
                </button>
              )}
              <div className="admin-gallery-details">
                <span className="admin-category-badge">
                  {CATEGORY_LABELS[item.category] || 'Other'}
                </span>
                <h4>{item.title || 'Untitled'}</h4>
                <p>{item.description || 'No story yet'}</p>
                <div className="admin-gallery-actions">
                  <button type="button" onClick={() => startEditing(item)} className="admin-btn admin-btn-ghost">
                    Edit
                  </button>
                  <a
                    className="admin-btn admin-btn-ghost"
                    href={`/gallery/${item.id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View
                  </a>
                  <button type="button" onClick={() => handleDelete(item.id)} className="admin-btn btn-danger">
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}

        {!loading && items.length === 0 && !error && (
          <div className="admin-gallery-empty">No images in this category yet.</div>
        )}
      </div>

      {editing && (
        <div className="admin-modal" role="presentation" onClick={() => setEditing(null)}>
          <div
            className="admin-modal-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="admin-gallery-edit-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="admin-modal-head">
              <h3 id="admin-gallery-edit-title">Edit gallery item</h3>
              <button
                type="button"
                className="admin-modal-close"
                onClick={() => setEditing(null)}
                aria-label="Close edit dialog"
              >
                <span aria-hidden="true">&times;</span>
              </button>
            </div>

            <div className="admin-modal-preview">
              <GalleryMedia item={editing} />
            </div>

            <form onSubmit={handleSaveEdit} className="admin-modal-form">
              <label className="admin-field-label" htmlFor="edit-title">Title</label>
              <input
                id="edit-title"
                type="text"
                className="admin-input"
                value={editing.title}
                onChange={(e) => setEditing({ ...editing, title: e.target.value })}
                required
                autoFocus
              />

              <label className="admin-field-label" htmlFor="edit-description">Short story</label>
              <textarea
                id="edit-description"
                className="admin-input"
                rows={4}
                maxLength={500}
                value={editing.description}
                onChange={(e) => setEditing({ ...editing, description: e.target.value })}
                placeholder="Tell the story: the occasion, the flavours, what makes this cake special..."
              />
              <p className="admin-blog-help">{editing.description.length} / 500 characters</p>

              <label className="admin-field-label" htmlFor="edit-category">Category</label>
              <select
                id="edit-category"
                className="admin-input"
                value={editing.category}
                onChange={(e) => setEditing({ ...editing, category: e.target.value })}
              >
                {CATEGORY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>

              {editError && <p className="admin-inline-error">{editError}</p>}

              <div className="admin-modal-actions">
                <button type="button" className="admin-btn admin-btn-ghost" onClick={() => setEditing(null)}>
                  Cancel
                </button>
                <button type="submit" className="admin-btn" disabled={savingEdit}>
                  {savingEdit ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
