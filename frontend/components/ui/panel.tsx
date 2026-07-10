import React from "react";

import { cx } from "@/lib/utils";

export function Panel({ children, className }: { children: React.ReactNode; className?: string }) {
  return <section className={cx("border border-[var(--border)] bg-[var(--panel)]", className)}>{children}</section>;
}
