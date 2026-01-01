"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="section">
      <h1>Something went wrong</h1>
      <p className="muted">
        If this persists, the API may be temporarily unavailable.
      </p>
      <p style={{ marginTop: 12 }}>
        <button className="cta" onClick={() => reset()}>
          Retry
        </button>
      </p>
    </div>
  );
}
