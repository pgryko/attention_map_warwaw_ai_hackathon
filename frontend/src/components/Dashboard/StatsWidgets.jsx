import { cn } from "../../lib/utils";

const statConfigs = [
  {
    key: "total",
    label: "Total",
    getValue: (stats) => stats.total_events || 0,
    icon: "📊",
    bgColor: "bg-blue-50 dark:bg-blue-900/20",
    textColor: "text-blue-600 dark:text-blue-400",
  },
  {
    key: "new",
    label: "New",
    getValue: (stats) => stats.events_by_status?.new || 0,
    icon: "🆕",
    bgColor: "bg-red-50 dark:bg-red-900/20",
    textColor: "text-red-600 dark:text-red-400",
  },
  {
    key: "verified",
    label: "Verified",
    getValue: (stats) => stats.events_by_status?.verified || 0,
    icon: "✅",
    bgColor: "bg-amber-50 dark:bg-amber-900/20",
    textColor: "text-amber-600 dark:text-amber-400",
  },
  {
    key: "critical",
    label: "Critical",
    getValue: (stats) => stats.events_by_severity?.["4"] || 0,
    icon: "🚨",
    bgColor: "bg-red-50 dark:bg-red-900/20",
    textColor: "text-red-600 dark:text-red-400",
  },
  {
    key: "clusters",
    label: "Clusters",
    getValue: (stats) => stats.active_clusters || 0,
    icon: "📍",
    bgColor: "bg-purple-50 dark:bg-purple-900/20",
    textColor: "text-purple-600 dark:text-purple-400",
  },
];

export default function StatsWidgets({ stats }) {
  if (!stats) return null;

  return (
    <div className="flex gap-2 overflow-x-auto border-b bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-800 sm:gap-4">
      {statConfigs.map((config) => {
        const value = config.getValue(stats);
        return (
          <div
            key={config.key}
            className={cn(
              "flex min-w-[100px] flex-shrink-0 items-center gap-2 rounded-lg px-3 py-2 sm:min-w-[120px]",
              config.bgColor,
            )}
          >
            <span className="text-lg sm:text-xl">{config.icon}</span>
            <div>
              <p
                className={cn("text-lg font-bold sm:text-xl", config.textColor)}
              >
                {value}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {config.label}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
