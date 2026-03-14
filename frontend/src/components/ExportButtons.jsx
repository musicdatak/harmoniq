import { useState } from "react";
import client from "../api/client";
import { useToast } from "./Toast";

export default function ExportButtons({ playlistId, playlistName }) {
  const [downloading, setDownloading] = useState(false);
  const toast = useToast();

  const handleDownloadExcel = async () => {
    setDownloading(true);
    try {
      const response = await client.get(
        `/api/playlists/${playlistId}/export/excel`,
        { responseType: "blob" }
      );
      const blob = new Blob([response.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${(playlistName || "playlist").replace(/\s+/g, "_")}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Excel downloaded");
    } catch {
      toast.error("Download failed");
    } finally {
      setDownloading(false);
    }
  };

  const handleCopyText = async () => {
    try {
      const { data } = await client.get(
        `/api/playlists/${playlistId}/export/text`
      );
      await navigator.clipboard.writeText(data);
      toast.success("Copied to clipboard");
    } catch {
      toast.error("Failed to copy");
    }
  };

  return (
    <div className="flex flex-wrap gap-3">
      <button
        onClick={handleDownloadExcel}
        disabled={downloading}
        className="bg-dark-surface border border-gray-700 text-gray-200 font-medium px-5 py-2.5 rounded-lg hover:border-teal hover:text-teal transition disabled:opacity-50 flex items-center gap-2"
      >
        {downloading ? (
          <>
            <span className="w-4 h-4 border-2 border-teal border-t-transparent rounded-full animate-spin" />
            Downloading...
          </>
        ) : (
          "Download Excel"
        )}
      </button>

      <button
        onClick={handleCopyText}
        className="bg-dark-surface border border-gray-700 text-gray-200 font-medium px-5 py-2.5 rounded-lg hover:border-teal hover:text-teal transition flex items-center gap-2"
      >
        Copy as Text
      </button>
    </div>
  );
}
