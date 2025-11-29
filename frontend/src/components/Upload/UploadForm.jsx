import { useState, useRef } from "react";
import { useGeolocation } from "../../hooks/useGeolocation";
import { Button } from "../ui/Button";
import { Textarea, Select } from "../ui/Input";
import { Card, CardContent } from "../ui/Card";
import { EVENT_CATEGORIES } from "../../lib/constants";
import { cn } from "../../lib/utils";

export default function UploadForm({ onSubmit, loading }) {
  const fileInputRef = useRef(null);
  const [mediaFiles, setMediaFiles] = useState([]);
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const { location, error: geoError, loading: geoLoading } = useGeolocation();

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    // Create preview URLs for each file
    const newFiles = files.map((file) => ({
      file,
      preview: URL.createObjectURL(file),
      type: file.type.startsWith("video/") ? "video" : "image",
    }));

    setMediaFiles((prev) => [...prev, ...newFiles].slice(0, 5)); // Max 5 files
  };

  const removeFile = (index) => {
    setMediaFiles((prev) => {
      const updated = [...prev];
      URL.revokeObjectURL(updated[index].preview);
      updated.splice(index, 1);
      return updated;
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (mediaFiles.length === 0) {
      alert("Please select at least one photo or video");
      return;
    }

    if (!location) {
      alert("Location is required. Please enable location services.");
      return;
    }

    const formData = new FormData();
    mediaFiles.forEach((item) => {
      formData.append("media", item.file);
    });
    formData.append("latitude", location.latitude.toString());
    formData.append("longitude", location.longitude.toString());
    formData.append("description", description);
    if (category) {
      formData.append("category", category);
    }

    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Media Upload */}
      <Card>
        <CardContent className="pt-6">
          <label className="mb-3 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Photo or Video *
          </label>

          {/* Preview Grid */}
          {mediaFiles.length > 0 && (
            <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
              {mediaFiles.map((item, index) => (
                <div
                  key={index}
                  className="group relative aspect-square overflow-hidden rounded-lg bg-gray-100 dark:bg-gray-800"
                >
                  {item.type === "video" ? (
                    <video
                      src={item.preview}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <img
                      src={item.preview}
                      alt={`Preview ${index + 1}`}
                      className="h-full w-full object-cover"
                    />
                  )}
                  <button
                    type="button"
                    onClick={() => removeFile(index)}
                    className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-red-500 text-white opacity-0 transition-opacity group-hover:opacity-100"
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
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                  {item.type === "video" && (
                    <div className="absolute bottom-2 left-2 rounded bg-black/60 px-2 py-1 text-xs text-white">
                      Video
                    </div>
                  )}
                </div>
              ))}

              {/* Add more button */}
              {mediaFiles.length < 5 && (
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex aspect-square items-center justify-center rounded-lg border-2 border-dashed border-gray-300 text-gray-400 transition-colors hover:border-blue-500 hover:text-blue-500 dark:border-gray-600 dark:hover:border-blue-400"
                >
                  <svg
                    className="h-8 w-8"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4v16m8-8H4"
                    />
                  </svg>
                </button>
              )}
            </div>
          )}

          {/* Upload area */}
          {mediaFiles.length === 0 && (
            <div
              className={cn(
                "cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors",
                "border-gray-300 hover:border-blue-500 dark:border-gray-600 dark:hover:border-blue-400",
              )}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
                <svg
                  className="h-6 w-6 text-blue-600 dark:text-blue-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              </div>
              <p className="text-gray-600 dark:text-gray-400">
                Click to upload photos or videos
              </p>
              <p className="mt-1 text-sm text-gray-400 dark:text-gray-500">
                Up to 5 files, max 50MB each
              </p>
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,video/*"
            capture="environment"
            multiple
            onChange={handleFileChange}
            className="hidden"
          />
        </CardContent>
      </Card>

      {/* Category */}
      <Card>
        <CardContent className="pt-6">
          <Select
            label="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="">Select a category...</option>
            {Object.entries(EVENT_CATEGORIES).map(([key, config]) => (
              <option key={key} value={key}>
                {config.icon} {config.label}
              </option>
            ))}
          </Select>
        </CardContent>
      </Card>

      {/* Location */}
      <Card>
        <CardContent className="pt-6">
          <label className="mb-3 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Location
          </label>
          <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-800">
            {geoLoading && (
              <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                <svg
                  className="h-4 w-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Getting your location...
              </div>
            )}
            {geoError && (
              <div className="flex items-center gap-2 text-red-500">
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
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                {geoError}. Please enable location services.
              </div>
            )}
            {location && (
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
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
                    d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
                <span>
                  {location.latitude.toFixed(6)},{" "}
                  {location.longitude.toFixed(6)}
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Description */}
      <Card>
        <CardContent className="pt-6">
          <Textarea
            label="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What's happening? (e.g., 'Fire in the building', 'Car accident on main street')"
            rows={3}
          />
        </CardContent>
      </Card>

      {/* Submit */}
      <Button
        type="submit"
        className="w-full"
        size="lg"
        loading={loading}
        disabled={loading || mediaFiles.length === 0 || !location}
      >
        Submit Report
      </Button>
    </form>
  );
}
