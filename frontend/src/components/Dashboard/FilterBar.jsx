const CATEGORIES = [
  { value: "", label: "All Categories" },
  { value: "emergency", label: "Emergency" },
  { value: "security", label: "Security" },
  { value: "traffic", label: "Traffic" },
  { value: "protest", label: "Protest" },
  { value: "infrastructure", label: "Infrastructure" },
  { value: "environmental", label: "Environmental" },
  { value: "informational", label: "Informational" },
];

const STATUSES = [
  { value: "", label: "All Statuses" },
  { value: "new", label: "New" },
  { value: "reviewing", label: "Reviewing" },
  { value: "verified", label: "Verified" },
  { value: "resolved", label: "Resolved" },
  { value: "false_alarm", label: "False Alarm" },
];

const SEVERITIES = [
  { value: "", label: "All Severities" },
  { value: "4", label: "Critical (4)" },
  { value: "3", label: "High (3)" },
  { value: "2", label: "Medium (2)" },
  { value: "1", label: "Low (1)" },
];

export default function FilterBar({ filters, onFilterChange }) {
  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value });
  };

  return (
    <div className="bg-white border-b px-4 py-2 flex gap-4 items-center">
      <span className="text-sm font-medium text-gray-600">Filters:</span>

      <select
        className="border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
        className="border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
        className="border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        value={filters.severity || ""}
        onChange={(e) => handleChange("severity", e.target.value)}
      >
        {SEVERITIES.map((sev) => (
          <option key={sev.value} value={sev.value}>
            {sev.label}
          </option>
        ))}
      </select>

      {(filters.category || filters.status || filters.severity) && (
        <button
          className="text-sm text-blue-600 hover:text-blue-800"
          onClick={() => onFilterChange({})}
        >
          Clear Filters
        </button>
      )}
    </div>
  );
}
