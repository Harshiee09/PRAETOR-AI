import Link from "next/link";
export default function NotFound() {
  return (
    <div className="about-content">
      <div className="eyebrow">PAGE NOT FOUND</div>
      <h1>
        Let’s get back
        <br />
        to the research.
      </h1>
      <Link href="/" className="primary-button">
        Open research workspace
      </Link>
    </div>
  );
}
