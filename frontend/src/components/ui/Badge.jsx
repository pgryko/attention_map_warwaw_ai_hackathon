import { cn } from "../../lib/utils";
import { EVENT_STATUSES, EVENT_CATEGORIES } from "../../lib/constants";

const variants = {
  default: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200",
  primary: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  success:
    "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
  warning: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  danger: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
};

const sizes = {
  sm: "px-2 py-0.5 text-xs",
  md: "px-2.5 py-1 text-xs",
  lg: "px-3 py-1 text-sm",
};

export function Badge({
  children,
  variant = "default",
  size = "md",
  className,
  ...props
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full font-medium",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status, size = "md" }) {
  const statusConfig = EVENT_STATUSES[status];
  if (!statusConfig) return null;

  const variantMap = {
    new: "danger",
    verified: "warning",
    in_progress: "primary",
    resolved: "success",
    rejected: "default",
  };

  return (
    <Badge variant={variantMap[status] || "default"} size={size}>
      {statusConfig.label}
    </Badge>
  );
}

export function CategoryBadge({ category, size = "md", showIcon = true }) {
  const categoryConfig = EVENT_CATEGORIES[category];
  if (!categoryConfig) return null;

  return (
    <Badge variant="default" size={size}>
      {showIcon && <span className="mr-1">{categoryConfig.icon}</span>}
      {categoryConfig.label}
    </Badge>
  );
}
