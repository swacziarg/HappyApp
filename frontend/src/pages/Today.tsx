import { useEffect, useState, type JSX } from "react";

/* ────────────────────────
   Types
──────────────────────── */

type Confidence = "low" | "medium" | "high";

type TodayOk = {
  status: "ok";
  date: string;
  predicted_mood: number;
  confidence: Confidence;
  explanation: string[];
};

type TodayState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "not_computed"; reason: string }
  | TodayOk;

/**
 * /history API response shape
 */
type HistoryApiResponse = {
  start: string;
  end: string;
  days: HistoryDay[];
};

type HistoryDay = {
  date: string;
  predicted_mood: number;
  confidence: Confidence;
  status: "available" | "missing";
};

/* ────────────────────────
   Config
──────────────────────── */

const API_BASE = "http://localhost:8000";

/* ────────────────────────
   Component
──────────────────────── */

export default function Today() {
  const [state, setState] = useState<TodayState>({ status: "loading" });

  /* ───────── Fetch (dev: Dec 20 via /history) ───────── */

  useEffect(() => {
    fetch(`${API_BASE}/history?start=2025-12-21&end=2025-12-21`)
      .then((res: Response) => {
        if (!res.ok) {
          throw new Error("Failed to fetch /history");
        }
        return res.json() as Promise<HistoryApiResponse>;
      })
      .then((data) => {
        if (!data.days || data.days.length === 0) {
          setState({
            status: "not_computed",
            reason: "No data for this date",
          });
          return;
        }

        const day = data.days[0];

        if (day.status !== "available") {
          setState({
            status: "not_computed",
            reason: "No prediction computed for this date",
          });
          return;
        }

        // Explicit history → today mapping
        setState({
          status: "ok",
          date: day.date,
          predicted_mood: day.predicted_mood,
          confidence: day.confidence,
          explanation: [
            "Historical view: explanation not stored for this day",
          ],
        });
      })
      .catch((err: Error) => {
        setState({ status: "error", message: err.message });
      });
  }, []);

  /* ───────── Derived presentation ───────── */

  let moodEmoji = "🙂";
  let moodDisplay: string | null = null;
  let explanationBlock: JSX.Element | null = null;
  let confidenceText: Confidence | null = null;

  if (state.status === "loading") {
    explanationBlock = (
      <p className="text-center text-sm text-gray-500">Loading…</p>
    );
  }

  if (state.status === "error") {
    explanationBlock = (
      <p className="text-center text-sm text-red-600">
        Error: {state.message}
      </p>
    );
  }

  if (state.status === "not_computed") {
    explanationBlock = (
      <p className="text-center text-sm text-gray-600">
        Not computed: {state.reason}
      </p>
    );
  }

  if (state.status === "ok") {
    const mood = state.predicted_mood;

    moodDisplay = `${mood.toFixed(1)} / 5.0`;
    confidenceText = state.confidence;

    if (mood <= 2) moodEmoji = "☹️";
    else if (mood < 3) moodEmoji = "😐";
    else if (mood < 4) moodEmoji = "🙂";
    else moodEmoji = "😊";

    explanationBlock = (
      <ul className="mt-3 space-y-1 text-center text-sm text-gray-600">
        {state.explanation.map((line, i) => (
          <li key={i}>{line}</li>
        ))}
      </ul>
    );
  }

  /* ───────── Render ───────── */

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-md">
        {/* Mood */}
        <div className="flex justify-center mb-2">
          <span className="text-7xl">{moodEmoji}</span>
        </div>

        {/* Numeric mood */}
        {moodDisplay && (
          <p className="text-center text-sm text-gray-500 mb-3">
            {moodDisplay}
          </p>
        )}

        {/* Title */}
        <h1 className="text-center text-xl font-semibold text-gray-900">
          Mood Today
        </h1>

        {/* Explanation */}
        {explanationBlock}

        {/* Divider */}
        <div className="my-5 h-px bg-gray-200" />

        {/* Confidence */}
        {confidenceText && (
          <p className="text-center text-sm text-gray-500">
            Confidence:{" "}
            <span className="font-medium text-gray-700">
              {confidenceText}
            </span>
          </p>
        )}
      </div>
    </div>
  );
}
