import { useRef } from "react";

// Netflix-style row: a title, an optional caption and posters that scroll sideways.
// The arrows sit in the heading, not over the posters, so they never cover a poster or title.
export default function MovieRow({ title, caption, children }) {
  const trackRef = useRef(null);
  const scroll = (direction) => {
    const track = trackRef.current;
    track?.scrollBy?.({ left: direction * track.clientWidth * 0.9, behavior: "smooth" });
  };

  return (
    <section className="movie-row" aria-label={title}>
      <div className="row-heading">
        <div>
          <h2>{title}</h2>
          {caption && <p className="row-caption">{caption}</p>}
        </div>
        <div className="row-arrows">
          <button type="button" className="row-arrow" aria-label={`Scroll ${title} left`} onClick={() => scroll(-1)}>
            ‹
          </button>
          <button type="button" className="row-arrow" aria-label={`Scroll ${title} right`} onClick={() => scroll(1)}>
            ›
          </button>
        </div>
      </div>
      <div className="row-track" ref={trackRef}>
        {children}
      </div>
    </section>
  );
}
