import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type JSX,
} from "react";
import { DayPicker } from "react-day-picker";
import "react-day-picker/dist/style.css";

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

type HistoryApiResponse = {
  start: string;
  end: string;
  days: HistoryDay[];
};

type HistoryDay = {
  date: string;
  predicted_mood: number;
  confidence: Confidence;
  explanation: string[];
  status: "available" | "missing";
};

const API_BASE = "http://localhost:8000";

/* ───────── Local-date helpers ───────── */

function todayISO() {
  return new Date().toLocaleDateString("en-CA");
}

function parseLocalDate(date: string) {
  const [y, m, d] = date.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function formatDate(date: string) {
  return parseLocalDate(date).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function monthBoundsFromDate(d: Date) {
  return {
    start: new Date(d.getFullYear(), d.getMonth(), 1).toLocaleDateString("en-CA"),
    end: new Date(d.getFullYear(), d.getMonth() + 1, 0).toLocaleDateString(
      "en-CA"
    ),
  };
}

/* ───────── Mood buckets ───────── */

function moodBucket(mood: number) {
  if (mood <= 2) return "low";
  if (mood < 4) return "medium";
  return "high";
}

/* ───────── Component ───────── */

export default function Today() {
  const [currentDate, setCurrentDate] = useState<string>(() => todayISO());
  const [visibleMonth, setVisibleMonth] = useState<Date>(() =>
    parseLocalDate(todayISO())
  );

  const [state, setState] = useState<TodayState>({ status: "loading" });
  const [history, setHistory] = useState<HistoryDay[]>([]);

  /** Tracks whether the user intentionally selected a date */
  const didSelectDateRef = useRef(false);

  /* ───────── Sync calendar only after date selection ───────── */

  useEffect(() => {
    if (!didSelectDateRef.current) return;

    const selected = parseLocalDate(currentDate);

    setVisibleMonth(
      new Date(selected.getFullYear(), selected.getMonth(), 1)
    );

    didSelectDateRef.current = false;
  }, [currentDate]);

  /* ───────── Fetch selected day ───────── */

  useEffect(() => {
    setState({ status: "loading" });

    fetch(`${API_BASE}/history?start=${currentDate}&end=${currentDate}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch /history");
        return res.json() as Promise<HistoryApiResponse>;
      })
      .then((data) => {
        const day = data.days?.[0];

        if (!day || day.status !== "available") {
          setState({
            status: "not_computed",
            reason: "No prediction computed for this date",
          });
          return;
        }

        setState({
          status: "ok",
          date: day.date,
          predicted_mood: day.predicted_mood,
          confidence: day.confidence,
          explanation: day.explanation,
        });
      })
      .catch((err: Error) => {
        setState({ status: "error", message: err.message });
      });
  }, [currentDate]);

  /* ───────── Fetch month for calendar coloring ───────── */

  useEffect(() => {
    const { start, end } = monthBoundsFromDate(visibleMonth);

    fetch(`${API_BASE}/history?start=${start}&end=${end}`)
      .then((res) => res.json() as Promise<HistoryApiResponse>)
      .then((data) => setHistory(data.days ?? []))
      .catch(() => setHistory([]));
  }, [visibleMonth]);

  /* ───────── Calendar modifiers ───────── */

  const modifiers = useMemo(() => {
    return {
      low: history
        .filter(
          (d) => d.status === "available" && moodBucket(d.predicted_mood) === "low"
        )
        .map((d) => parseLocalDate(d.date)),

      medium: history
        .filter(
          (d) =>
            d.status === "available" && moodBucket(d.predicted_mood) === "medium"
        )
        .map((d) => parseLocalDate(d.date)),

      high: history
        .filter(
          (d) => d.status === "available" && moodBucket(d.predicted_mood) === "high"
        )
        .map((d) => parseLocalDate(d.date)),
    };
  }, [history]);

  /* ───────── Derived UI ───────── */

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
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-md space-y-4">
        <DayPicker
          mode="single"
          month={visibleMonth}
          onMonthChange={setVisibleMonth}
          selected={parseLocalDate(currentDate)}
          onSelect={(date) => {
            if (!date) return;
            didSelectDateRef.current = true;
            setCurrentDate(date.toLocaleDateString("en-CA"));
          }}
          modifiers={modifiers}
          modifiersClassNames={{
            low: "bg-red-200",
            medium: "bg-yellow-200",
            high: "bg-green-200",
          }}
          disabled={{ after: new Date() }}
        />

        <div className="flex items-center justify-between">
          <button
            className="px-3 py-1 rounded-lg bg-gray-100 hover:bg-gray-200"
            onClick={() => {
              didSelectDateRef.current = true;
              setCurrentDate((d) =>
                new Date(
                  parseLocalDate(d).setDate(
                    parseLocalDate(d).getDate() - 1
                  )
                ).toLocaleDateString("en-CA")
              );
            }}
          >
            ←
          </button>

          <span className="text-sm font-medium text-gray-700">
            {formatDate(currentDate)}
          </span>

          <button
            className="px-3 py-1 rounded-lg bg-gray-100 hover:bg-gray-200"
            onClick={() => {
              didSelectDateRef.current = true;
              setCurrentDate((d) =>
                new Date(
                  parseLocalDate(d).setDate(
                    parseLocalDate(d).getDate() + 1
                  )
                ).toLocaleDateString("en-CA")
              );
            }}
          >
            →
          </button>
        </div>

        <div className="flex justify-center">
          <span className="text-7xl">{moodEmoji}</span>
        </div>

        {moodDisplay && (
          <p className="text-center text-sm text-gray-500">{moodDisplay}</p>
        )}

        <h1 className="text-center text-xl font-semibold text-gray-900">
          Mood
        </h1>

        {explanationBlock}

        <div className="my-4 h-px bg-gray-200" />

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
