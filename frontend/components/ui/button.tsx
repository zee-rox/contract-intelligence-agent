"use client";

import type { ButtonHTMLAttributes } from "react";
import React from "react";
import { cx } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
};

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  const styles = {
    primary: "bg-[var(--accent)] text-white hover:bg-[var(--accent-strong)]",
    secondary: "border border-[var(--border)] bg-[var(--panel)] hover:bg-[var(--panel-muted)]",
    ghost: "hover:bg-[var(--panel-muted)]",
    danger: "bg-[var(--danger)] text-white"
  };
  return (
    <button
      className={cx(
        "inline-flex h-10 items-center justify-center gap-2 rounded-md px-3 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50",
        styles[variant],
        className
      )}
      {...props}
    />
  );
}
