import { cn } from "../../lib/utils";

const sizes = {
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-8 w-8",
  xl: "h-12 w-12",
};

export function Spinner({ size = "md", className }) {
  return (
    <svg
      className={cn(
        "animate-spin text-blue-600 dark:text-blue-400",
        sizes[size],
        className,
      )}
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

export function LoadingOverlay({ message = "Loading..." }) {
  return (
    <div className="flex h-full min-h-[200px] flex-col items-center justify-center gap-3">
      <Spinner size="lg" />
      <p className="text-sm text-gray-500 dark:text-gray-400">{message}</p>
    </div>
  );
}

export function PageLoader() {
  return (
    <div className="flex h-screen items-center justify-center">
      <Spinner size="xl" />
    </div>
  );
}
