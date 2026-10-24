import { forwardRef, type InputHTMLAttributes } from "react";

/** forwardRef so React Hook Form's `register()` can attach to the real checkbox. */
export const CheckboxField = forwardRef<
  HTMLInputElement,
  { label: string } & InputHTMLAttributes<HTMLInputElement>
>(function CheckboxField({ label, id, ...props }, ref) {
  return (
    <label htmlFor={id} className="text-ink-3 flex items-center gap-2 text-[13px] font-semibold">
      <input ref={ref} id={id} type="checkbox" className="accent-primary size-4" {...props} />
      {label}
    </label>
  );
});
