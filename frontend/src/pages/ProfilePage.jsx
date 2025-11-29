import { useQuery } from "@tanstack/react-query";
import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { getUserStats } from "../api/auth";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import {
  ProfileStatsSkeleton,
  BadgeGridSkeleton,
} from "../components/ui/Skeleton";
import { QUERY_KEYS } from "../lib/constants";

export default function ProfilePage() {
  const { user, isAuthenticated, loading: authLoading } = useAuth();

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: [QUERY_KEYS.userStats],
    queryFn: getUserStats,
    enabled: isAuthenticated,
  });

  if (authLoading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <div className="mb-8 h-8 w-32 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardContent className="py-6">
              <ProfileStatsSkeleton />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-6">
              <ProfileStatsSkeleton />
            </CardContent>
          </Card>
          <Card className="md:col-span-2">
            <CardContent className="py-6">
              <BadgeGridSkeleton count={4} />
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: { pathname: "/profile" } }} />;
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-8 text-2xl font-bold text-gray-900 dark:text-white">
        Profile
      </h1>

      <div className="grid gap-6 md:grid-cols-2">
        {/* User Info */}
        <Card>
          <CardHeader>
            <CardTitle>Account</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Email
                </p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {user?.email}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Role</p>
                <Badge variant={user?.is_staff ? "primary" : "default"}>
                  {user?.is_staff ? "Staff" : "Citizen"}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats */}
        <Card>
          <CardHeader>
            <CardTitle>Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <ProfileStatsSkeleton />
            ) : stats ? (
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-blue-50 p-4 text-center dark:bg-blue-900/20">
                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {stats.reputation || 0}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Reputation
                  </p>
                </div>
                <div className="rounded-lg bg-emerald-50 p-4 text-center dark:bg-emerald-900/20">
                  <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                    {stats.report_count || 0}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Reports
                  </p>
                </div>
                <div className="rounded-lg bg-amber-50 p-4 text-center dark:bg-amber-900/20">
                  <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                    {stats.verified_count || 0}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Verified
                  </p>
                </div>
                <div className="rounded-lg bg-purple-50 p-4 text-center dark:bg-purple-900/20">
                  <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {stats.badges?.length || 0}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Badges
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-center text-gray-500 dark:text-gray-400">
                No stats available
              </p>
            )}
          </CardContent>
        </Card>

        {/* Badges */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Badges</CardTitle>
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <BadgeGridSkeleton count={4} />
            ) : stats?.badges && stats.badges.length > 0 ? (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
                {stats.badges.map((badge) => (
                  <div
                    key={badge.id}
                    className="flex flex-col items-center rounded-lg border p-4 dark:border-gray-700"
                  >
                    <span className="text-3xl">{badge.icon || "🏆"}</span>
                    <p className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                      {badge.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {badge.description}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-gray-500 dark:text-gray-400">
                No badges earned yet. Start reporting incidents to earn badges!
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
