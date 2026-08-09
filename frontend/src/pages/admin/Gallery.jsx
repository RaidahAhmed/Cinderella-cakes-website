import { useEffect, useState, useRef } from 'react';
import { fetchGallery, uploadGalleryItem, deleteGalleryItem, BASE_URL } from '../../lib/api';
import '../../styles/admin.css';

export default function Gallery() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  useEffect(() => {
    loadGallery();
  }, []);

  const loadGallery = async () => {
    try {
      const data = await fetchGallery();
      setItems(data);
    } catch (err) {
      console.error('Failed to load gallery', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this image?')) return;
    
    try {
      await deleteGalleryItem(id);
      setItems(items.filter(item => item.id !== id));
    } catch (err) {
      alert('Failed to delete image');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!fileInputRef.current.files[0]) {
      alert('Please select an image to upload.');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('image', fileInputRef.current.files[0]);
    if (title) formData.append('title', title);
    if (description) formData.append('description', description);

    try {
      const res = await uploadGalleryItem(formData);
      if (res.success) {
        // Reset form and reload gallery
        fileInputRef.current.value = '';
        setTitle('');
        setDescription('');
        loadGallery();
      } else {
        alert(res.error || 'Upload failed');
      }
    } catch (err) {
      alert('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  if (loading) return <div>Loading gallery...</div>;

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Gallery Management</h1>
      </div>

      <div className="admin-card" style={{ marginBottom: '24px' }}>
        <h3>Upload New Image</h3>
        <form onSubmit={handleUpload} style={{ display: 'flex', gap: '16px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '4px' }}>Image File</label>
            <input type="file" accept="image/*" ref={fileInputRef} required />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '4px' }}>Title (Optional)</label>
            <input 
              type="text" 
              value={title} 
              onChange={e => setTitle(e.target.value)} 
              placeholder="E.g., Wedding Cake"
              className="admin-input"
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '4px' }}>Description (Optional)</label>
            <input 
              type="text" 
              value={description} 
              onChange={e => setDescription(e.target.value)}
              placeholder="Short description..." 
              className="admin-input"
            />
          </div>
          <button type="submit" className="admin-btn" disabled={uploading}>
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
        </form>
      </div>

      <div className="admin-gallery-grid">
        {items.map(item => (
          <div key={item.id} className="admin-gallery-item">
            <div 
              className="admin-gallery-image"
              style={{ backgroundImage: `url(${BASE_URL}/static/uploads/inspiration/${item.image_url})` }}
            ></div>
            <div className="admin-gallery-details">
              <h4>{item.title || 'Untitled'}</h4>
              <p>{item.description || 'No description'}</p>
              <button 
                onClick={() => handleDelete(item.id)}
                className="admin-btn btn-danger"
                style={{ width: '100%', marginTop: '8px' }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <div style={{ padding: '24px', gridColumn: '1 / -1', textAlign: 'center', color: '#666' }}>
            No images in gallery yet.
          </div>
        )}
      </div>
    </div>
  );
}
