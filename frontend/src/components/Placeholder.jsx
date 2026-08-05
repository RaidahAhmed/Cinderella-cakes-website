/**
 * A clearly-marked stand-in for a real photo. Swap these out later by
 * dropping an <img> where <Placeholder /> currently sits - see each page
 * file for exactly which ones to replace and with what.
 */
export default function Placeholder({ label, minHeight }) {
  return (
    <div className="placeholder" style={minHeight ? { minHeight } : undefined}>
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path
          d="M4 16l4.5-6 3.5 4.5 2.5-3L20 16H4z"
          fill="currentColor"
          opacity="0.6"
        />
        <rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="1.5" />
        <circle cx="8" cy="8.5" r="1.5" fill="currentColor" />
      </svg>
      <span>{label}</span>
    </div>
  );
}
