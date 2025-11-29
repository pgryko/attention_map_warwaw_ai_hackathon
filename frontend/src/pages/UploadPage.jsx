import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import UploadForm from "../components/Upload/UploadForm";
import { uploadEvent } from "../api/client";

export default function UploadPage() {
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (formData) => {
    try {
      setUploading(true);
      setError(null);
      await uploadEvent(formData);
      setSuccess(true);
      setTimeout(() => navigate("/"), 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <Link to="/" className="text-gray-600 hover:text-gray-900">
            &larr; Back to Dashboard
          </Link>
          <h1 className="text-xl font-bold text-gray-900">Report Event</h1>
          <div className="w-20"></div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-2xl mx-auto py-8 px-4">
        {success ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
            <div className="text-green-600 text-4xl mb-4">checkmark</div>
            <h2 className="text-lg font-semibold text-green-800">
              Event Reported Successfully
            </h2>
            <p className="text-green-600 mt-2">
              Your report is being processed. Redirecting to dashboard...
            </p>
          </div>
        ) : (
          <>
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <p className="text-red-600">{error}</p>
              </div>
            )}
            <UploadForm onSubmit={handleSubmit} loading={uploading} />
          </>
        )}
      </main>
    </div>
  );
}
