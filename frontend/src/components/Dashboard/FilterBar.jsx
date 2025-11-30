import { useState, useCallback } from "react";
import {
  EVENT_CATEGORIES,
  EVENT_STATUSES,
  SEVERITY_LEVELS,
  TIME_FILTERS,
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

const TIME_OPTIONS = Object.entries(TIME_FILTERS).map(([value, config]) => ({
  value,
  label: config.label,
}));

export default function FilterBar({ filters, onFilterChange }) {
  const [searchInput, setSearchInput] = useState(filters.search || "");

  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value });
  };

  // Debounced search handler
  const handleSearchChange = useCallback(
    (e) => {
      const value = e.target.value;
      setSearchInput(value);
      // Update filter after a short delay to avoid too many updates
      const timeoutId = setTimeout(() => {
        onFilterChange({ ...filters, search: value || undefined });
      }, 300);
      return () => clearTimeout(timeoutId);
    },
    [filters, onFilterChange]
  );

  const hasFilters =
    filters.category ||
    filters.status ||
    filters.severity ||
    filters.timeRange ||
    filters.search;

  const clearFilters = () => {
    setSearchInput("");
    onFilterChange({});
  };

  return (
    <div className="flex flex-wrap items-center gap-3 border-b bg-white px-4 py-2 dark:border-gray-700 dark:bg-gray-800">
      {/* Search input */}
      <div className="relative">
        <svg
          className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          type="text"
          placeholder="Search events..."
          value={searchInput}
          onChange={handleSearchChange}
          className="w-40 rounded-lg border border-gray-300 bg-white py-1.5 pl-9 pr-3 text-sm transition-colors placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:placeholder:text-gray-500 sm:w-48"
        />
      </div>

      <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
        Filters:
      </span>

      {/* Time filter */}
      <select
        className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
        value={filters.timeRange || ""}
        onChange={(e) => handleChange("timeRange", e.target.value)}
      >
        {TIME_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

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
          onClick={clearFilters}
        >
          Clear Filters
        </button>
      )}
    </div>
  );
}
