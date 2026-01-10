import { useRef, useState } from "react";
import { authFetch } from "../api/authFetch";
import { API_BASE_URL } from "../api/config";

type UploadState =
  | { status: "idle" }
  | { status: "uploading" }
  | { status: "success"; daysIngested: number; daysPredicted: number }
  | { status: "error"; message: string };

export function GarminUpload() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [state, setState] = useState<UploadState>({ status: "idle" });

  async function uploadFiles(files: FileList) {
    if (!files.length) return;

    const form = new FormData();
    Array.from(files).forEach((f) => form.append("files", f));

    setState({ status: "uploading" });

    try {
      const res = await authFetch(`${API_BASE_URL}/garmin/upload`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Upload failed");
      }

      const json = await res.json();
      setState({
        status: "success",
        daysIngested: json.days_ingested,
        daysPredicted: json.days_predicted,
      });
    } catch (err) {
      setState({
        status: "error",
        message:
          err instanceof Error
            ? err.message
            : "Something went wrong during upload",
      });
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    uploadFiles(e.dataTransfer.files);
  }

  return (
    <div className="mt-8">
      <div
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
        className="
          cursor-pointer rounded-2xl border-2 border-dashed
          border-gray-300 bg-white/60 p-6
          text-center transition
          hover:border-indigo-400 hover:bg-white
        "
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".zip,.json"
          className="hidden"
          onChange={(e) =>
            e.target.files && uploadFiles(e.target.files)
          }
        />

        {state.status === "idle" && (
          <>
            <div className="text-3xl">📤</div>
            <p className="mt-2 text-sm font-medium">
              Upload Garmin data
            </p>
            <p className="mt-1 text-xs text-gray-500">
              Drag & drop a Garmin export ZIP or JSON files
            </p>
          </>
        )}

        {state.status === "uploading" && (
          <>
            <div className="animate-pulse text-3xl">⏳</div>
            <p className="mt-2 text-sm text-gray-600">
              Processing Garmin data…
            </p>
          </>
        )}

        {state.status === "success" && (
          <>
            <div className="text-3xl">✅</div>
            <p className="mt-2 text-sm font-medium">
              Upload complete
            </p>
            <p className="mt-1 text-xs text-gray-500">
              {state.daysIngested} days ingested ·{" "}
              {state.daysPredicted} predictions updated
            </p>
          </>
        )}

        {state.status === "error" && (
          <>
            <div className="text-3xl">⚠️</div>
            <p className="mt-2 text-sm font-medium text-red-600">
              Upload failed
            </p>
            <p className="mt-1 text-xs text-gray-500">
              {state.message}
            </p>
          </>
        )}
      </div>
    </div>
  );
}
