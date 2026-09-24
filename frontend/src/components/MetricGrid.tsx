import type { KpiItem } from "../types";

interface MetricGridProps {
  items: KpiItem[];
}

export function MetricGrid({ items }: MetricGridProps) {
  return (
    <section className="metric-grid" aria-label="关键指标">
      {items.map((item) => (
        <article className="metric-card" key={item.label}>
          <span>{item.label}</span>
          <strong className="metric-value">{item.value}</strong>
          <small>{item.trend}</small>
        </article>
      ))}
    </section>
  );
}
