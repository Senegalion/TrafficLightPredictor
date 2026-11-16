import type { ReactNode } from "react";

type Tone = "neutral" | "info" | "warning" | "success" | "danger";

export function Badge({ tone = "neutral", children, title }: { tone?: Tone; children: ReactNode; title?: string }) {
  return (
    <span className={`badge badge--${tone}`} title={title}>
      {children}
    </span>
  );
}
