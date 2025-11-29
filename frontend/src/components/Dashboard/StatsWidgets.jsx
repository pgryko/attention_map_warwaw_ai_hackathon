export default function StatsWidgets({ stats }) {
  const widgets = [
    {
      label: "Total Events",
      value: stats.total_events,
      color: "text-blue-600",
    },
    {
      label: "New",
      value: stats.events_by_status?.new || 0,
      color: "text-blue-600",
    },
    {
      label: "Reviewing",
      value: stats.events_by_status?.reviewing || 0,
      color: "text-purple-600",
    },
    {
      label: "Critical",
      value: stats.events_by_severity?.["4"] || 0,
      color: "text-red-600",
    },
    {
      label: "Active Clusters",
      value: stats.active_clusters,
      color: "text-orange-600",
    },
  ];

  return (
    <div className="bg-white border-b px-4 py-2 flex gap-6">
      {widgets.map((widget) => (
        <div key={widget.label} className="flex items-center gap-2">
          <span className={`text-2xl font-bold ${widget.color}`}>
            {widget.value}
          </span>
          <span className="text-sm text-gray-500">{widget.label}</span>
        </div>
      ))}
    </div>
  );
}
