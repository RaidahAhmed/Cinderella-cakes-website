import { useEffect, useState } from 'react';
import {
  fetchPageBySlug,
  updateHeroSection,
  updateContentSection,
  updateContentBlock,
} from '../../lib/api';
import '../../styles/admin.css';

const PAGE_SLUGS = ['home', 'about'];

export default function ContentEditor() {
  const [pages, setPages] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(null);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    loadPages();
  }, []);

  const loadPages = async () => {
    try {
      const results = {};
      for (const slug of PAGE_SLUGS) {
        const data = await fetchPageBySlug(slug);
        if (data) results[slug] = data;
      }
      setPages(results);
    } catch (err) {
      console.error('Failed to load pages', err);
    } finally {
      setLoading(false);
    }
  };

  const handleHeroSave = async (heroId, heroData) => {
    setSaving(`hero-${heroId}`);
    setMessage(null);
    try {
      await updateHeroSection(heroId, heroData);
      setMessage({ type: 'success', text: 'Hero section updated!' });
      loadPages();
    } catch {
      setMessage({ type: 'error', text: 'Failed to update hero section.' });
    } finally {
      setSaving(null);
    }
  };

  const handleSectionSave = async (sectionId, sectionData) => {
    setSaving(`section-${sectionId}`);
    setMessage(null);
    try {
      await updateContentSection(sectionId, sectionData);
      setMessage({ type: 'success', text: 'Section updated!' });
      loadPages();
    } catch {
      setMessage({ type: 'error', text: 'Failed to update section.' });
    } finally {
      setSaving(null);
    }
  };

  const handleBlockSave = async (blockId, blockData) => {
    setSaving(`block-${blockId}`);
    setMessage(null);
    try {
      await updateContentBlock(blockId, blockData);
      setMessage({ type: 'success', text: 'Content block updated!' });
      loadPages();
    } catch {
      setMessage({ type: 'error', text: 'Failed to update content block.' });
    } finally {
      setSaving(null);
    }
  };

  if (loading) return <div>Loading content...</div>;

  const msgStyle = (type) => ({
    padding: '12px',
    marginBottom: '16px',
    borderRadius: '4px',
    backgroundColor: type === 'success' ? '#e6f4ea' : '#fce8e6',
    color: type === 'success' ? '#137333' : '#c5221f',
  });

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Edit Page Content</h1>
      </div>

      {message && <div style={msgStyle(message.type)}>{message.text}</div>}

      {Object.entries(pages).map(([slug, page]) => (
        <div key={slug} style={{ marginBottom: '40px' }}>
          <h2 style={{ color: 'var(--purple-dark)', textTransform: 'capitalize', marginBottom: '16px' }}>
            {page.title || slug} Page
          </h2>

          {/* Hero Section */}
          {page.hero && (
            <HeroEditor
              hero={page.hero}
              onSave={handleHeroSave}
              saving={saving}
            />
          )}

          {/* Content Sections */}
          {page.sections && page.sections.map((section) => (
            <SectionEditor
              key={section.id}
              section={section}
              onSectionSave={handleSectionSave}
              onBlockSave={handleBlockSave}
              saving={saving}
            />
          ))}
        </div>
      ))}

      {Object.keys(pages).length === 0 && (
        <div className="admin-card">
          <p style={{ color: '#666' }}>No pages found. Run the seed script to create default pages.</p>
        </div>
      )}
    </div>
  );
}

function HeroEditor({ hero, onSave, saving }) {
  const [form, setForm] = useState({
    eyebrow: hero.eyebrow || '',
    heading: hero.heading || '',
    heading_accent: hero.heading_accent || '',
    subheading: hero.subheading || '',
    primary_button_text: hero.primary_button_text || '',
    secondary_button_text: hero.secondary_button_text || '',
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  return (
    <div className="admin-card">
      <h3 style={{ marginBottom: '16px', color: 'var(--teal)' }}>Hero Banner</h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div>
          <label style={labelStyle}>Eyebrow Text</label>
          <input name="eyebrow" value={form.eyebrow} onChange={handleChange} className="admin-input" style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>Heading</label>
          <input name="heading" value={form.heading} onChange={handleChange} className="admin-input" style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>Heading Accent</label>
          <input name="heading_accent" value={form.heading_accent} onChange={handleChange} className="admin-input" style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>Subheading</label>
          <input name="subheading" value={form.subheading} onChange={handleChange} className="admin-input" style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>Primary Button Text</label>
          <input name="primary_button_text" value={form.primary_button_text} onChange={handleChange} className="admin-input" style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>Secondary Button Text</label>
          <input name="secondary_button_text" value={form.secondary_button_text} onChange={handleChange} className="admin-input" style={inputStyle} />
        </div>
      </div>
      <button
        onClick={() => onSave(hero.id, form)}
        className="admin-btn"
        disabled={saving === `hero-${hero.id}`}
        style={{ marginTop: '12px' }}
      >
        {saving === `hero-${hero.id}` ? 'Saving...' : 'Save Hero'}
      </button>
    </div>
  );
}

function SectionEditor({ section, onSectionSave, onBlockSave, saving }) {
  const [form, setForm] = useState({
    eyebrow: section.eyebrow || '',
    heading: section.heading || '',
    subheading: section.subheading || '',
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  return (
    <div className="admin-card">
      <h3 style={{ marginBottom: '16px', color: 'var(--teal)' }}>
        Section: {section.section_type || 'Content'}
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div>
          <label style={labelStyle}>Eyebrow</label>
          <input name="eyebrow" value={form.eyebrow} onChange={handleChange} className="admin-input" style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>Heading</label>
          <input name="heading" value={form.heading} onChange={handleChange} className="admin-input" style={inputStyle} />
        </div>
        <div style={{ gridColumn: '1 / -1' }}>
          <label style={labelStyle}>Subheading</label>
          <textarea name="subheading" value={form.subheading} onChange={handleChange} className="admin-input" style={{ ...inputStyle, minHeight: '60px' }} />
        </div>
      </div>
      <button
        onClick={() => onSectionSave(section.id, form)}
        className="admin-btn"
        disabled={saving === `section-${section.id}`}
        style={{ marginTop: '12px' }}
      >
        {saving === `section-${section.id}` ? 'Saving...' : 'Save Section'}
      </button>

      {/* Content Blocks */}
      {section.blocks && section.blocks.length > 0 && (
        <div style={{ marginTop: '20px', borderTop: '1px solid var(--border-soft)', paddingTop: '16px' }}>
          <h4 style={{ color: 'var(--ink-soft)', marginBottom: '12px' }}>Content Blocks</h4>
          {section.blocks.map((block) => (
            <BlockEditor key={block.id} block={block} onSave={onBlockSave} saving={saving} />
          ))}
        </div>
      )}
    </div>
  );
}

function BlockEditor({ block, onSave, saving }) {
  const [form, setForm] = useState({
    title: block.title || '',
    text: block.text || '',
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  return (
    <div style={{ marginBottom: '16px', padding: '12px', background: 'var(--cream)', borderRadius: '8px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div>
          <label style={labelStyle}>Title</label>
          <input name="title" value={form.title} onChange={handleChange} className="admin-input" style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>Text</label>
          <textarea name="text" value={form.text} onChange={handleChange} className="admin-input" style={{ ...inputStyle, minHeight: '60px' }} />
        </div>
      </div>
      <button
        onClick={() => onSave(block.id, form)}
        className="admin-btn"
        disabled={saving === `block-${block.id}`}
        style={{ marginTop: '8px', fontSize: '.85rem', padding: '8px 16px' }}
      >
        {saving === `block-${block.id}` ? 'Saving...' : 'Save Block'}
      </button>
    </div>
  );
}

const labelStyle = { display: 'block', marginBottom: '4px', fontWeight: 'bold', fontSize: '.85rem' };
const inputStyle = { width: '100%' };

