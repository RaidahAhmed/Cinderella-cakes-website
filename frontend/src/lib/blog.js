// Small helpers shared by the public blog pages and the admin article editor.

// "19 November 2026"
export function formatBlogDate(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
}

// Articles are plain text: a blank line starts a new paragraph and a line that
// begins with "## " is a heading. Returns [{ type: 'h2' | 'p', text }].
export function parseArticle(content) {
  return String(content || '')
    .replace(/\r\n/g, '\n')
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean)
    .map((block) =>
      block.startsWith('## ')
        ? { type: 'h2', text: block.slice(3).trim() }
        : { type: 'p', text: block },
    );
}

// Rough reading time so visitors know what they are opening.
export function readingMinutes(content) {
  const words = String(content || '').trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / 200));
}
