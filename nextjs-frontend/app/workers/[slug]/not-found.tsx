"use client";

export default function NotFound() {
  return (
    <div className="section">
      <h1>Worker not found</h1>
      <p className="muted">
        The worker you’re looking for doesn’t exist (or was removed).
      </p>
      <p style={{ marginTop: 12 }}>
        <a className="cta" href="/">
          Back to directory
        </a>
      </p>
    </div>
  );
}
