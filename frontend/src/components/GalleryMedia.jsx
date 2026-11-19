import { isVideoMedia, resolveMediaUrl } from '../lib/api';

// Keep one rendering contract for gallery cards, previews, and selected order designs.
export default function GalleryMedia({ item, className, onPlay }) {
  const src = resolveMediaUrl(item?.image_url);
  const label = item?.title || 'Cake gallery design';
  if (isVideoMedia(item)) {
    return (
      <video
        key={src}
        className={className}
        src={src}
        controls
        preload="metadata"
        playsInline
        tabIndex={0}
        aria-label={`Video: ${label}`}
        onPlay={onPlay}
      >
        Your browser cannot play this video. <a href={src}>Open {label}</a>.
      </video>
    );
  }
  return <img className={className} src={src} alt={label} loading="lazy" />;
}
