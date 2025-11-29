import { useState, useRef } from "react";
import { useGeolocation } from "../../hooks/useGeolocation";

export default function UploadForm({ onSubmit, loading }) {
  const fileInputRef = useRef(null);
  const [media, setMedia] = useState(null);
  const [mediaPreview, setMediaPreview] = useState(null);
  const [description, setDescription] = useState("");
  const { location, error: geoError, loading: geoLoading } = useGeolocation();

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setMedia(file);
      // Create preview URL
      const previewUrl = URL.createObjectURL(file);
      setMediaPreview(previewUrl);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!media) {
      alert("Please select a photo or video");
      return;
    }

    if (!location) {
      alert("Location is required. Please enable location services.");
      return;
    }

    const formData = new FormData();
    formData.append("media", media);
    formData.append("latitude", location.latitude.toString());
    formData.append("longitude", location.longitude.toString());
    formData.append("description", description);

    onSubmit(formData);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-lg shadow p-6 space-y-6"
    >
      {/* Media Upload */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Photo or Video *
        </label>
        <div
          className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-500 transition"
          onClick={() => fileInputRef.current?.click()}
        >
          {mediaPreview ? (
            <div className="relative">
              {media?.type.startsWith("video/") ? (
                <video
                  src={mediaPreview}
                  className="max-h-64 mx-auto rounded"
                  controls
                />
              ) : (
                <img
                  src={mediaPreview}
                  alt="Preview"
                  className="max-h-64 mx-auto rounded"
                />
              )}
              <button
                type="button"
                className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1"
                onClick={(e) => {
                  e.stopPropagation();
                  setMedia(null);
                  setMediaPreview(null);
                }}
              >
                X
              </button>
            </div>
          ) : (
            <div>
              <div className="text-4xl text-gray-400 mb-2">camera</div>
              <p className="text-gray-600">Click to upload photo or video</p>
              <p className="text-sm text-gray-400">Max 50MB</p>
            </div>
          )}
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,video/*"
          capture="environment"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {/* Location */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Location
        </label>
        <div className="bg-gray-50 rounded-lg p-4">
          {geoLoading && (
            <p className="text-gray-500">Getting your location...</p>
          )}
          {geoError && (
            <p className="text-red-500">
              Location error: {geoError}. Please enable location services.
            </p>
          )}
          {location && (
            <div className="flex items-center gap-2">
              <span className="text-green-600">location pin</span>
              <span className="text-gray-700">
                {location.latitude.toFixed(6)}, {location.longitude.toFixed(6)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description (optional)
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What's happening? (e.g., 'Fire in the building', 'Car accident on main street')"
          className="w-full border rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={3}
        />
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={loading || !media || !location}
        className={`w-full py-3 rounded-lg font-medium transition ${
          loading || !media || !location
            ? "bg-gray-300 text-gray-500 cursor-not-allowed"
            : "bg-blue-600 text-white hover:bg-blue-700"
        }`}
      >
        {loading ? "Submitting..." : "Submit Report"}
      </button>
    </form>
  );
}
