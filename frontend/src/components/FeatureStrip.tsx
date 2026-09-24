import type { FeatureItem } from "../types";

interface FeatureStripProps {
  items: FeatureItem[];
}

export function FeatureStrip({ items }: FeatureStripProps) {
  return (
    <section className="feature-strip" aria-label="核心功能">
      {items.map((item) => (
        <article className="feature-panel" key={item.title}>
          <span className="pill">{item.metric}</span>
          <strong>{item.title}</strong>
          <p>{item.description}</p>
        </article>
      ))}
    </section>
  );
}
