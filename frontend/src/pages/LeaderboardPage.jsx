import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getLeaderboard } from "../api/auth";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../components/ui/Card";
import { Spinner } from "../components/ui/Spinner";
import { QUERY_KEYS } from "../lib/constants";
import { cn } from "../lib/utils";

const TIME_PERIODS = [
  { id: "all", label: "All Time", days: null },
  { id: "month", label: "This Month", days: 30 },
  { id: "week", label: "This Week", days: 7 },
];

export default function LeaderboardPage() {
  const [timePeriod, setTimePeriod] = useState("all");

  const selectedPeriod = TIME_PERIODS.find((p) => p.id === timePeriod);

  const {
    data: leaderboard,
    isLoading,
    error,
  } = useQuery({
    queryKey: [QUERY_KEYS.leaderboard, timePeriod],
    queryFn: () => getLeaderboard(20, selectedPeriod?.days),
  });

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-8 text-2xl font-bold text-gray-900 dark:text-white">
        Leaderboard
      </h1>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Top Reporters</CardTitle>
            {/* Time period tabs */}
            <div className="flex gap-1 rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
              {TIME_PERIODS.map((period) => (
                <button
                  key={period.id}
                  onClick={() => setTimePeriod(period.id)}
                  className={cn(
                    "rounded-md px-3 py-1 text-xs font-medium transition-colors",
                    timePeriod === period.id
                      ? "bg-white text-blue-600 shadow-sm dark:bg-gray-700 dark:text-blue-400"
                      : "text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
                  )}
                >
                  {period.label}
                </button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <p className="text-center text-red-500">
              Failed to load leaderboard
            </p>
          ) : leaderboard && leaderboard.length > 0 ? (
            <div className="divide-y dark:divide-gray-700">
              {leaderboard.map((entry, index) => (
                <div
                  key={entry.user_id || index}
                  className="flex items-center gap-4 py-4"
                >
                  {/* Rank */}
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800">
                    {index === 0 ? (
                      <span className="text-xl">🥇</span>
                    ) : index === 1 ? (
                      <span className="text-xl">🥈</span>
                    ) : index === 2 ? (
                      <span className="text-xl">🥉</span>
                    ) : (
                      <span className="font-bold text-gray-500 dark:text-gray-400">
                        {index + 1}
                      </span>
                    )}
                  </div>

                  {/* User info */}
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-gray-900 dark:text-white">
                      {entry.display_name ||
                        entry.email?.split("@")[0] ||
                        "Anonymous"}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {entry.badge_count || 0} badges
                    </p>
                  </div>

                  {/* Reputation */}
                  <div className="text-right">
                    <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
                      {entry.reputation || 0}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      points
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">
              No users on the leaderboard yet. Be the first to report an
              incident!
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
