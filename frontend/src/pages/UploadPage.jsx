import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import UploadForm from "../components/Upload/UploadForm";
import { uploadEvent } from "../api/client";
import { Card, CardContent } from "../components/ui/Card";
import { QUERY_KEYS } from "../lib/constants";

export default function UploadPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [success, setSuccess] = useState(false);

  const mutation = useMutation({
    mutationFn: uploadEvent,
    onSuccess: (data) => {
      // Invalidate events query to refresh the list
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.events] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.stats] });
      setSuccess(true);
      // Navigate to event detail or dashboard after delay
      setTimeout(() => {
        if (data?.id) {
          navigate(`/event/${data.id}`);
        } else {
          navigate("/");
        }
      }, 2000);
    },
  });

  const handleSubmit = (formData) => {
    mutation.mutate(formData);
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      {/* Back link */}
      <Link
        to="/"
        className="mb-6 inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
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
        Back to Dashboard
      </Link>

      <h1 className="mb-6 text-2xl font-bold text-gray-900 dark:text-white">
        Report an Incident
      </h1>

      {success ? (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
              <svg
                className="h-8 w-8 text-emerald-600 dark:text-emerald-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Report Submitted!
            </h2>
            <p className="mt-2 text-gray-500 dark:text-gray-400">
              Your report is being processed. Redirecting...
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {mutation.isError && (
            <Card className="mb-6 border-red-200 dark:border-red-800">
              <CardContent className="py-4">
                <div className="flex items-center gap-3 text-red-600 dark:text-red-400">
                  <svg
                    className="h-5 w-5 flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <span>
                    {mutation.error?.message ||
                      "Upload failed. Please try again."}
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          <UploadForm onSubmit={handleSubmit} loading={mutation.isPending} />
        </>
      )}
    </div>
  );
}
