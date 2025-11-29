import { cn } from "../../lib/utils";

export function Card({ children, className, ...props }) {
  return (
    <div
      className={cn(
        "rounded-lg border bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className, ...props }) {
  return (
    <div
      className={cn("border-b px-4 py-3 dark:border-gray-700", className)}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({ children, className, ...props }) {
  return (
    <h3
      className={cn(
        "text-lg font-semibold text-gray-900 dark:text-gray-100",
        className,
      )}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardContent({ children, className, ...props }) {
  return (
    <div className={cn("px-4 py-3", className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({ children, className, ...props }) {
  return (
    <div
      className={cn("border-t px-4 py-3 dark:border-gray-700", className)}
      {...props}
    >
      {children}
    </div>
  );
}
