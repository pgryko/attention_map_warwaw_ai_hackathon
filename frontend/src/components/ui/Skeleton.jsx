import { cn } from "../../lib/utils";

export function Skeleton({ className, ...props }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-gray-200 dark:bg-gray-700",
        className,
      )}
      {...props}
    />
  );
}

export function EventCardSkeleton() {
  return (
    <div className="border-b p-4 dark:border-gray-700">
      <div className="flex gap-3">
        <Skeleton className="h-12 w-12 flex-shrink-0 rounded-full" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
          <div className="flex gap-2">
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-5 w-20 rounded-full" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function EventFeedSkeleton({ count = 5 }) {
  return (
    <div>
      {Array.from({ length: count }).map((_, i) => (
        <EventCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function StatsWidgetSkeleton() {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-white p-4 shadow-sm dark:bg-gray-800">
      <Skeleton className="h-10 w-10 rounded-full" />
      <div className="space-y-2">
        <Skeleton className="h-6 w-12" />
        <Skeleton className="h-3 w-16" />
      </div>
    </div>
  );
}

export function StatsBarSkeleton() {
  return (
    <div className="flex gap-4 overflow-x-auto border-b bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-800">
      {Array.from({ length: 4 }).map((_, i) => (
        <StatsWidgetSkeleton key={i} />
      ))}
    </div>
  );
}

export function ProfileStatsSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="rounded-lg bg-gray-50 p-4 dark:bg-gray-800">
          <Skeleton className="mx-auto h-8 w-12" />
          <Skeleton className="mx-auto mt-2 h-3 w-16" />
        </div>
      ))}
    </div>
  );
}

export function BadgeGridSkeleton({ count = 8 }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="flex flex-col items-center rounded-lg border p-4 dark:border-gray-700"
        >
          <Skeleton className="h-12 w-12 rounded-full" />
          <Skeleton className="mt-2 h-4 w-20" />
          <Skeleton className="mt-1 h-3 w-24" />
        </div>
      ))}
    </div>
  );
}

export function MapSkeleton() {
  return (
    <div className="relative h-full w-full bg-gray-200 dark:bg-gray-800">
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <Skeleton className="mx-auto h-12 w-12 rounded-full" />
          <Skeleton className="mx-auto mt-3 h-4 w-24" />
        </div>
      </div>
      {/* Fake map grid lines */}
      <div className="absolute inset-0 opacity-10">
        <div className="grid h-full grid-cols-4 grid-rows-4">
          {Array.from({ length: 16 }).map((_, i) => (
            <div
              key={i}
              className="border border-gray-400 dark:border-gray-600"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
