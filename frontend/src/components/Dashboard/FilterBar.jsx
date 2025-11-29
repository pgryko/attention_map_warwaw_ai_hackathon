import {
  EVENT_CATEGORIES,
  EVENT_STATUSES,
  SEVERITY_LEVELS,
} from "../../lib/constants";

const CATEGORIES = [
  { value: "", label: "All Categories" },
  ...Object.entries(EVENT_CATEGORIES).map(([value, config]) => ({
    value,
    label: `${config.icon} ${config.label}`,
  })),
];

const STATUSES = [
  { value: "", label: "All Statuses" },
  ...Object.entries(EVENT_STATUSES).map(([value, config]) => ({
    value,
    label: config.label,
  })),
];

const SEVERITIES = [
  { value: "", label: "All Severities" },
  ...Object.entries(SEVERITY_LEVELS)
    .reverse()
    .map(([value, config]) => ({
      value,
      label: `${config.label} (${value})`,
    })),
];

export default function FilterBar({ filters, onFilterChange }) {
  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value });
  };

  const hasFilters = filters.category || filters.status || filters.severity;

  return (
    <div className="flex flex-wrap items-center gap-3 border-b bg-white px-4 py-2 dark:border-gray-700 dark:bg-gray-800">
      <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
        Filters:
      </span>

      <select
        className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
        value={filters.category || ""}
        onChange={(e) => handleChange("category", e.target.value)}
      >
        {CATEGORIES.map((cat) => (
          <option key={cat.value} value={cat.value}>
            {cat.label}
          </option>
        ))}
      </select>

      <select
        className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
        value={filters.status || ""}
        onChange={(e) => handleChange("status", e.target.value)}
      >
        {STATUSES.map((status) => (
          <option key={status.value} value={status.value}>
            {status.label}
          </option>
        ))}
      </select>

      <select
        className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
        value={filters.severity || ""}
        onChange={(e) => handleChange("severity", e.target.value)}
      >
        {SEVERITIES.map((sev) => (
          <option key={sev.value} value={sev.value}>
            {sev.label}
          </option>
        ))}
      </select>

      {hasFilters && (
        <button
          className="text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
          onClick={() => onFilterChange({})}
        >
          Clear Filters
        </button>
      )}
    </div>
  );
}
