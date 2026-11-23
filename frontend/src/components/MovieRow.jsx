import { useRef } from "react";

// Netflix-style row: a title, an optional caption and posters that scroll sideways.
export default function MovieRow({ title, caption, children }) {
  const trackRef = useRef(null);
  const scroll = (direction) => {
    const track = trackRef.current;
    track?.scrollBy?.({ left: direction * track.clientWidth * 0.9, behavior: "smooth" });
  };

  return (
    <section className="movie-row" aria-label={title}>
      <div className="row-heading">
        <h2>{title}</h2>
        {caption && <p className="row-caption">{caption}</p>}
      </div>
      <div className="row-body">
        <button type="button" className="row-arrow left" aria-label={`Scroll ${title} left`} onClick={() => scroll(-1)}>
          ‹
        </button>
        <div className="row-track" ref={trackRef}>
          {children}
        </div>
        <button
          type="button"
          className="row-arrow right"
          aria-label={`Scroll ${title} right`}
          onClick={() => scroll(1)}
        >
          ›
        </button>
      </div>
    </section>
  );
}
