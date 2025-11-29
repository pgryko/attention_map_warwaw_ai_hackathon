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

export default function LeaderboardPage() {
  const {
    data: leaderboard,
    isLoading,
    error,
  } = useQuery({
    queryKey: [QUERY_KEYS.leaderboard],
    queryFn: () => getLeaderboard(20),
  });

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-8 text-2xl font-bold text-gray-900 dark:text-white">
        Leaderboard
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Top Reporters</CardTitle>
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
