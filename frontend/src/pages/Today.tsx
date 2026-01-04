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

/* ───────── Date helpers ───────── */

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

function moodBucket(mood: number) {
  if (mood <= 2) return "low";
  if (mood < 4) return "medium";
  return "high";
}

/* ───────── Component ───────── */

export default function Today() {
  const [currentDate, setCurrentDate] = useState(todayISO);
  const [visibleMonth, setVisibleMonth] = useState(() =>
    parseLocalDate(todayISO())
  );

  const [state, setState] = useState<TodayState>({ status: "loading" });
  const [history, setHistory] = useState<HistoryDay[]>([]);

  const didSelectDateRef = useRef(false);

  /* ───────── Sync calendar after date selection ───────── */

  useEffect(() => {
    if (!didSelectDateRef.current) return;
    const d = parseLocalDate(currentDate);
    setVisibleMonth(new Date(d.getFullYear(), d.getMonth(), 1));
    didSelectDateRef.current = false;
  }, [currentDate]);

  /* ───────── Fetch selected day ───────── */

  useEffect(() => {
    setState({ status: "loading" });

    fetch(`${API_BASE}/history?start=${currentDate}&end=${currentDate}`)
      .then((r) => r.json() as Promise<HistoryApiResponse>)
      .then((data) => {
        const day = data.days?.[0];
        if (!day || day.status !== "available") {
          setState({
            status: "not_computed",
            reason: "No prediction for this date",
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
      .catch((e) => setState({ status: "error", message: e.message }));
  }, [currentDate]);

  /* ───────── Fetch month for calendar coloring ───────── */

  useEffect(() => {
    const { start, end } = monthBoundsFromDate(visibleMonth);
    fetch(`${API_BASE}/history?start=${start}&end=${end}`)
      .then((r) => r.json() as Promise<HistoryApiResponse>)
      .then((d) => setHistory(d.days ?? []))
      .catch(() => setHistory([]));
  }, [visibleMonth]);

  /* ───────── Calendar modifiers ───────── */

  const modifiers = useMemo(() => {
    return {
      low: history
        .filter(
          (d) =>
            d.status === "available" &&
            d.confidence !== "low" &&
            moodBucket(d.predicted_mood) === "low"
        )
        .map((d) => parseLocalDate(d.date)),
  
      medium: history
        .filter(
          (d) =>
            d.status === "available" &&
            d.confidence !== "low" &&
            moodBucket(d.predicted_mood) === "medium"
        )
        .map((d) => parseLocalDate(d.date)),
  
      high: history
        .filter(
          (d) =>
            d.status === "available" &&
            d.confidence !== "low" &&
            moodBucket(d.predicted_mood) === "high"
        )
        .map((d) => parseLocalDate(d.date)),
  
      /** 👇 NEW **/
      lowConfidence: history
        .filter((d) => d.status === "available" && d.confidence === "low")
        .map((d) => parseLocalDate(d.date)),
  
      missing: history
        .filter((d) => d.status === "missing")
        .map((d) => parseLocalDate(d.date)),
    };
  }, [history]);
  

  /* ───────── Derived UI ───────── */

  let emoji = "🙂";
  let explanationBlock: JSX.Element | null = null;
  let moodText: JSX.Element | null = null;

  if (state.status === "loading") {
    explanationBlock = <p className="text-center text-sm text-gray-500">Loading…</p>;
  }

  if (state.status === "error") {
    explanationBlock = (
      <p className="text-center text-sm text-red-600">{state.message}</p>
    );
  }

  if (state.status === "not_computed") {
    explanationBlock = (
      <p className="text-center text-sm text-gray-600">{state.reason}</p>
    );
  }

  if (state.status === "ok") {
    const { predicted_mood, confidence } = state;

    if (predicted_mood <= 2) emoji = "☹️";
    else if (predicted_mood < 3) emoji = "😐";
    else if (predicted_mood < 4) emoji = "🙂";
    else emoji = "😊";

    if (confidence === "low") {
      moodText = (
        <p className="text-center text-sm text-gray-400 italic">
          Not enough data to personalize this day
        </p>
      );
      emoji = "⚪️";
    } else {
      moodText = (
        <p className="text-center text-sm text-gray-500">
          {predicted_mood.toFixed(1)} / 5.0
        </p>
      );
    }

    explanationBlock =
      confidence === "low" ? null : (
        <ul className="mt-3 space-y-1 text-center text-sm text-gray-600">
          {state.explanation.map((e, i) => (
            <li key={i}>{e}</li>
          ))}
        </ul>
      );
  }

  /* ───────── Render ───────── */

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-md space-y-4">
        <DayPicker
          mode="single"
          month={visibleMonth}
          onMonthChange={setVisibleMonth}
          selected={parseLocalDate(currentDate)}
          onSelect={(d) => {
            if (!d) return;
            didSelectDateRef.current = true;
            setCurrentDate(d.toLocaleDateString("en-CA"));
          }}
          modifiers={modifiers}
          modifiersClassNames={{
            low: "bg-red-200",
            medium: "bg-yellow-200",
            high: "bg-green-200",

            lowConfidence:
              "bg-gray-200 text-gray-400 opacity-60",

            missing:
              "text-gray-300 opacity-40",
          }}
          disabled={{ after: new Date() }}
        />

        <div className="flex items-center justify-between">
          <button
            className="px-3 py-1 bg-gray-100 rounded-lg"
            onClick={() => {
              didSelectDateRef.current = true;
              setCurrentDate((d) =>
                new Date(parseLocalDate(d).setDate(parseLocalDate(d).getDate() - 1))
                  .toLocaleDateString("en-CA")
              );
            }}
          >
            ←
          </button>

          <span className="text-sm font-medium">{formatDate(currentDate)}</span>

          <button
            className="px-3 py-1 bg-gray-100 rounded-lg"
            onClick={() => {
              didSelectDateRef.current = true;
              setCurrentDate((d) =>
                new Date(parseLocalDate(d).setDate(parseLocalDate(d).getDate() + 1))
                  .toLocaleDateString("en-CA")
              );
            }}
          >
            →
          </button>
        </div>

        <div className="flex justify-center text-7xl">{emoji}</div>
        {moodText}

        <h1 className="text-center text-xl font-semibold">Mood</h1>
        {explanationBlock}
      </div>
    </div>
  );
}
