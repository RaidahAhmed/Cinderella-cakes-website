import { useEffect, useState } from 'react';
import { fetchAdminSettings, updateAdminSettings } from '../../lib/api';
import '../../styles/admin.css';

export default function Settings() {
  const [settings, setSettings] = useState({
    site_name: '',
    contact_email: '',
    contact_phone: '',
    address: '',
    business_hours: '',
    logo_url: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await fetchAdminSettings();
      if (data) {
        setSettings({
          site_name: data.site_name || '',
          contact_email: data.contact_email || '',
          contact_phone: data.contact_phone || '',
          address: data.address || '',
          business_hours: data.business_hours || '',
          logo_url: data.logo_url || ''
        });
      }
    } catch (err) {
      console.error('Failed to load settings', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setSettings({
      ...settings,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      await updateAdminSettings(settings);
      setMessage({ type: 'success', text: 'Settings updated successfully!' });
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to update settings.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Loading settings...</div>;

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Site Settings</h1>
      </div>

      <div className="admin-card" style={{ maxWidth: '600px' }}>
        {message && (
          <div style={{
            padding: '12px', 
            marginBottom: '16px', 
            borderRadius: '4px',
            backgroundColor: message.type === 'success' ? '#e6f4ea' : '#fce8e6',
            color: message.type === 'success' ? '#137333' : '#c5221f'
          }}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>Site Name</label>
            <input 
              type="text" 
              name="site_name"
              value={settings.site_name} 
              onChange={handleChange}
              className="admin-input"
              style={{ width: '100%' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>Contact Email</label>
            <input 
              type="email" 
              name="contact_email"
              value={settings.contact_email} 
              onChange={handleChange}
              className="admin-input"
              style={{ width: '100%' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>Contact Phone</label>
            <input 
              type="text" 
              name="contact_phone"
              value={settings.contact_phone} 
              onChange={handleChange}
              className="admin-input"
              style={{ width: '100%' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>Address</label>
            <textarea 
              name="address"
              value={settings.address} 
              onChange={handleChange}
              className="admin-input"
              style={{ width: '100%', minHeight: '80px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>Business Hours</label>
            <textarea 
              name="business_hours"
              value={settings.business_hours} 
              onChange={handleChange}
              className="admin-input"
              style={{ width: '100%', minHeight: '80px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>Logo URL</label>
            <input 
              type="text" 
              name="logo_url"
              value={settings.logo_url} 
              onChange={handleChange}
              className="admin-input"
              style={{ width: '100%' }}
            />
          </div>
          
          <button type="submit" className="admin-btn" disabled={saving} style={{ marginTop: '16px' }}>
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </form>
      </div>
    </div>
  );
}
