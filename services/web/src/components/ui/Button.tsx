import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

const VARIANTS: Record<Variant, string> = {
  primary: "border-0 bg-primary text-white hover:bg-primary-dark",
  secondary: "border border-line-strong bg-surface text-ink hover:bg-canvas",
  ghost: "border-0 bg-transparent text-muted hover:text-ink",
  danger: "border border-danger-line bg-surface text-danger hover:bg-danger-soft",
};

const SIZES: Record<Size, string> = {
  sm: "min-h-9 px-3 text-[13px]",
  md: "min-h-10 px-4 text-sm",
  lg: "min-h-11 px-[18px] text-sm",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export function Button({
  variant = "primary",
  size = "md",
  type = "button",
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`inline-flex cursor-pointer items-center justify-center gap-2 rounded-[10px] font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    />
  );
}
