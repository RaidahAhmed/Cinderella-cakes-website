import { useEffect, useState } from 'react';
import { fetchAdminSettings, updateAdminSettings, changePassword } from '../../lib/api';
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

  // Password change state
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [pwSaving, setPwSaving] = useState(false);
  const [pwMessage, setPwMessage] = useState(null);

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

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPwMessage(null);

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPwMessage({ type: 'error', text: 'New passwords do not match.' });
      return;
    }
    if (passwordForm.newPassword.length < 6) {
      setPwMessage({ type: 'error', text: 'New password must be at least 6 characters.' });
      return;
    }

    setPwSaving(true);
    try {
      const res = await changePassword(passwordForm.currentPassword, passwordForm.newPassword);
      if (res.success) {
        setPwMessage({ type: 'success', text: 'Password changed successfully!' });
        setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
      } else {
        setPwMessage({ type: 'error', text: res.message || 'Failed to change password.' });
      }
    } catch (err) {
      setPwMessage({ type: 'error', text: 'Failed to change password.' });
    } finally {
      setPwSaving(false);
    }
  };

  if (loading) return <div>Loading settings...</div>;

  const msgStyle = (type) => ({
    padding: '12px',
    marginBottom: '16px',
    borderRadius: '4px',
    backgroundColor: type === 'success' ? '#e6f4ea' : '#fce8e6',
    color: type === 'success' ? '#137333' : '#c5221f'
  });

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Site Settings</h1>
      </div>

      <div className="admin-card" style={{ maxWidth: '600px' }}>
        {message && (
          <div style={msgStyle(message.type)}>
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

      {/* Password Change Section */}
      <div className="admin-card" style={{ maxWidth: '600px', marginTop: '32px' }}>
        <h3 style={{ marginBottom: '16px', color: 'var(--purple-dark)' }}>Change Password</h3>
        {pwMessage && (
          <div style={msgStyle(pwMessage.type)}>
            {pwMessage.text}
          </div>
        )}

        <form onSubmit={handlePasswordChange} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>Current Password</label>
            <input
              type="password"
              value={passwordForm.currentPassword}
              onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
              className="admin-input"
              style={{ width: '100%' }}
              required
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>New Password</label>
            <input
              type="password"
              value={passwordForm.newPassword}
              onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
              className="admin-input"
              style={{ width: '100%' }}
              required
              minLength={6}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>Confirm New Password</label>
            <input
              type="password"
              value={passwordForm.confirmPassword}
              onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
              className="admin-input"
              style={{ width: '100%' }}
              required
              minLength={6}
            />
          </div>
          <button type="submit" className="admin-btn" disabled={pwSaving} style={{ marginTop: '8px' }}>
            {pwSaving ? 'Changing...' : 'Change Password'}
          </button>
        </form>
      </div>
    </div>
  );
}
