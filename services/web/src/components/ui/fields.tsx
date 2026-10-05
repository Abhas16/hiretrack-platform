import { forwardRef, type InputHTMLAttributes, type SelectHTMLAttributes } from "react";

const LABEL = "flex flex-col gap-1.5 text-[13px] font-semibold text-ink-3";
const CONTROL =
  "min-h-11 rounded-[10px] border border-line-strong bg-surface px-3.5 text-sm font-normal text-ink outline-none focus:border-primary";

interface FieldProps {
  label: string;
  error?: string;
}

/** forwardRef so React Hook Form's `register()` can attach to the real <input>. */
export const TextField = forwardRef<
  HTMLInputElement,
  FieldProps & InputHTMLAttributes<HTMLInputElement>
>(function TextField({ label, error, id, ...props }, ref) {
  return (
    <label htmlFor={id} className={LABEL}>
      {label}
      <input ref={ref} id={id} aria-invalid={!!error} className={CONTROL} {...props} />
      {error && <span className="text-danger text-xs font-medium">{error}</span>}
    </label>
  );
});

export const SelectField = forwardRef<
  HTMLSelectElement,
  FieldProps &
    SelectHTMLAttributes<HTMLSelectElement> & { options: { value: string; label: string }[] }
>(function SelectField({ label, error, id, options, ...props }, ref) {
  return (
    <label htmlFor={id} className={LABEL}>
      {label}
      <select ref={ref} id={id} className={`${CONTROL} px-2.5`} {...props}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && <span className="text-danger text-xs font-medium">{error}</span>}
    </label>
  );
});
