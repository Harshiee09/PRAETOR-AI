"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <div className="about-content" role="alert">
      <h1>
        Something interrupted
        <br />
        the workspace.
      </h1>
      <p>
        Try loading this view again. If the problem continues, refresh the page.
      </p>
      <button className="primary-button" onClick={reset}>
        Try again
      </button>
    </div>
  );
}
