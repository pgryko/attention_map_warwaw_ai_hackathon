import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getEvent, updateEventStatus } from "../api/client";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/ui/Button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../components/ui/Card";
import { StatusBadge, CategoryBadge } from "../components/ui/Badge";
import { Spinner } from "../components/ui/Spinner";
import { Textarea } from "../components/ui/Input";
import { formatRelativeTime } from "../lib/utils";
import { QUERY_KEYS, MAP_CONFIG } from "../lib/constants";
import { MapContainer, TileLayer, Marker } from "react-leaflet";
import { useState } from "react";
import "leaflet/dist/leaflet.css";

export default function EventDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isStaff } = useAuth();
  const [triageNotes, setTriageNotes] = useState("");

  const {
    data: event,
    isLoading,
    error,
  } = useQuery({
    queryKey: [QUERY_KEYS.event, id],
    queryFn: () => getEvent(id),
  });

  const statusMutation = useMutation({
    mutationFn: ({ status, notes }) => updateEventStatus(id, status, notes),
    onSuccess: () => {
      queryClient.invalidateQueries([QUERY_KEYS.event, id]);
      queryClient.invalidateQueries([QUERY_KEYS.events]);
      setTriageNotes("");
    },
  });

  const handleStatusChange = (newStatus) => {
    statusMutation.mutate({ status: newStatus, notes: triageNotes });
  };

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-red-500">Event not found or failed to load.</p>
            <Button
              variant="ghost"
              onClick={() => navigate(-1)}
              className="mt-4"
            >
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="mb-4 flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
      >
        <svg
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
        Back
      </button>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Header */}
          <Card>
            <CardContent className="py-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <CategoryBadge category={event.category} />
                    <StatusBadge status={event.status} />
                  </div>
                  <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                    {event.title || `${event.category} Incident`}
                  </h1>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Reported {formatRelativeTime(event.created_at)}
                    {event.reporter_name && ` by ${event.reporter_name}`}
                  </p>
                </div>
                {event.severity && (
                  <div
                    className={`rounded-full px-3 py-1 text-sm font-medium ${
                      event.severity >= 4
                        ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
                        : event.severity >= 3
                          ? "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300"
                          : event.severity >= 2
                            ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300"
                            : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                    }`}
                  >
                    Severity: {event.severity}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Description */}
          {event.description && (
            <Card>
              <CardHeader>
                <CardTitle>Description</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {event.description}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Transcription */}
          {event.transcription && (
            <Card>
              <CardHeader>
                <CardTitle>Audio Transcription</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap italic">
                  &ldquo;{event.transcription}&rdquo;
                </p>
              </CardContent>
            </Card>
          )}

          {/* Media */}
          {event.media_urls && event.media_urls.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Media</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-2">
                  {event.media_urls.map((url, index) => (
                    <div
                      key={index}
                      className="overflow-hidden rounded-lg bg-gray-100 dark:bg-gray-800"
                    >
                      {url.endsWith(".mp4") || url.endsWith(".webm") ? (
                        <video
                          src={url}
                          controls
                          className="h-48 w-full object-cover"
                        />
                      ) : (
                        <img
                          src={url}
                          alt={`Media ${index + 1}`}
                          className="h-48 w-full object-cover"
                        />
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Staff Triage Panel */}
          {isStaff && (
            <Card className="border-blue-200 dark:border-blue-800">
              <CardHeader className="bg-blue-50 dark:bg-blue-900/20">
                <CardTitle className="text-blue-700 dark:text-blue-300">
                  Staff Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                <Textarea
                  label="Notes (optional)"
                  value={triageNotes}
                  onChange={(e) => setTriageNotes(e.target.value)}
                  placeholder="Add notes about this incident..."
                  rows={2}
                />
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button
                    variant="success"
                    onClick={() => handleStatusChange("verified")}
                    loading={statusMutation.isPending}
                    disabled={event.status === "verified"}
                  >
                    Verify
                  </Button>
                  <Button
                    variant="primary"
                    onClick={() => handleStatusChange("in_progress")}
                    loading={statusMutation.isPending}
                    disabled={event.status === "in_progress"}
                  >
                    In Progress
                  </Button>
                  <Button
                    variant="success"
                    onClick={() => handleStatusChange("resolved")}
                    loading={statusMutation.isPending}
                    disabled={event.status === "resolved"}
                  >
                    Resolve
                  </Button>
                  <Button
                    variant="danger"
                    onClick={() => handleStatusChange("rejected")}
                    loading={statusMutation.isPending}
                    disabled={event.status === "rejected"}
                  >
                    Reject
                  </Button>
                </div>
                {statusMutation.isError && (
                  <p className="mt-2 text-sm text-red-500">
                    Failed to update status. Please try again.
                  </p>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar - Map */}
        <div className="lg:col-span-1">
          <Card className="sticky top-20">
            <CardHeader>
              <CardTitle>Location</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="h-64 w-full">
                {event.latitude && event.longitude ? (
                  <MapContainer
                    center={[event.latitude, event.longitude]}
                    zoom={15}
                    className="h-full w-full rounded-b-lg"
                    scrollWheelZoom={false}
                  >
                    <TileLayer
                      attribution={MAP_CONFIG.attribution}
                      url={MAP_CONFIG.tileLayer}
                    />
                    <Marker position={[event.latitude, event.longitude]} />
                  </MapContainer>
                ) : (
                  <div className="flex h-full items-center justify-center bg-gray-100 dark:bg-gray-800 rounded-b-lg">
                    <p className="text-gray-500 dark:text-gray-400">
                      No location data
                    </p>
                  </div>
                )}
              </div>
              {event.address && (
                <div className="px-4 py-3 border-t dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {event.address}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
