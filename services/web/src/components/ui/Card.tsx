import type { ReactNode } from "react";

interface CardProps {
  title?: string;
  subtitle?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Card({ title, subtitle, children, className = "" }: CardProps) {
  return (
    <section
      className={`border-line bg-surface flex flex-col gap-3.5 rounded-[14px] border p-5 ${className}`}
    >
      {(title || subtitle) && (
        <div className="flex flex-col gap-0.5">
          {title && <h3 className="m-0 text-[15px] font-bold">{title}</h3>}
          {subtitle && <span className="text-muted font-mono text-xs">{subtitle}</span>}
        </div>
      )}
      {children}
    </section>
  );
}
