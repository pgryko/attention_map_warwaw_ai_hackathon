import { forwardRef } from "react";
import { cn } from "../../lib/utils";

export const Input = forwardRef(function Input(
  { label, error, className, type = "text", ...props },
  ref,
) {
  return (
    <div className="w-full">
      {label && (
        <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}
      <input
        ref={ref}
        type={type}
        className={cn(
          "w-full rounded-lg border px-3 py-2 text-sm transition-colors",
          "bg-white dark:bg-gray-800",
          "text-gray-900 dark:text-gray-100",
          "placeholder-gray-400 dark:placeholder-gray-500",
          "focus:outline-none focus:ring-2 focus:ring-offset-0",
          error
            ? "border-red-500 focus:border-red-500 focus:ring-red-500"
            : "border-gray-300 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600",
          "disabled:cursor-not-allowed disabled:bg-gray-100 disabled:opacity-50 dark:disabled:bg-gray-900",
          className,
        )}
        {...props}
      />
      {error && <p className="mt-1.5 text-sm text-red-500">{error}</p>}
    </div>
  );
});

export const Textarea = forwardRef(function Textarea(
  { label, error, className, rows = 4, ...props },
  ref,
) {
  return (
    <div className="w-full">
      {label && (
        <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}
      <textarea
        ref={ref}
        rows={rows}
        className={cn(
          "w-full rounded-lg border px-3 py-2 text-sm transition-colors",
          "bg-white dark:bg-gray-800",
          "text-gray-900 dark:text-gray-100",
          "placeholder-gray-400 dark:placeholder-gray-500",
          "focus:outline-none focus:ring-2 focus:ring-offset-0",
          "resize-none",
          error
            ? "border-red-500 focus:border-red-500 focus:ring-red-500"
            : "border-gray-300 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600",
          "disabled:cursor-not-allowed disabled:bg-gray-100 disabled:opacity-50 dark:disabled:bg-gray-900",
          className,
        )}
        {...props}
      />
      {error && <p className="mt-1.5 text-sm text-red-500">{error}</p>}
    </div>
  );
});

export const Select = forwardRef(function Select(
  { label, error, className, children, ...props },
  ref,
) {
  return (
    <div className="w-full">
      {label && (
        <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}
      <select
        ref={ref}
        className={cn(
          "w-full rounded-lg border px-3 py-2 text-sm transition-colors",
          "bg-white dark:bg-gray-800",
          "text-gray-900 dark:text-gray-100",
          "focus:outline-none focus:ring-2 focus:ring-offset-0",
          error
            ? "border-red-500 focus:border-red-500 focus:ring-red-500"
            : "border-gray-300 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600",
          "disabled:cursor-not-allowed disabled:bg-gray-100 disabled:opacity-50 dark:disabled:bg-gray-900",
          className,
        )}
        {...props}
      >
        {children}
      </select>
      {error && <p className="mt-1.5 text-sm text-red-500">{error}</p>}
    </div>
  );
});
