import React from "react";

import { cx } from "@/lib/utils";

export function Badge({
  children,
  tone = "neutral"
}: {
  children: React.ReactNode;
  tone?: "neutral" | "low" | "medium" | "high" | "success" | "warning";
}) {
  const tones = {
    neutral: "border-[var(--border)] bg-[var(--panel-muted)]",
    low: "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
    medium: "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-200",
    high: "border-red-500/40 bg-red-500/10 text-red-700 dark:text-red-200",
    success: "border-[var(--accent)] bg-[color-mix(in_srgb,var(--accent),transparent_85%)]",
    warning: "border-[var(--warning)] bg-[color-mix(in_srgb,var(--warning),transparent_85%)]"
  };
  return <span className={cx("inline-flex rounded border px-2 py-0.5 text-xs font-medium", tones[tone])}>{children}</span>;
}
