import { useEffect, useRef, useState, type JSX } from "react";
import { MoodCalendar } from "../components/MoodCalendar";
import { useMoodHistory } from "../hooks/useMoodHistory";
import type { TodayState } from "../types/mood";
import {
  todayISO,
  parseLocalDate,
  formatDate,
} from "../utils/date";

export default function Today(): JSX.Element {
  const [currentDate, setCurrentDate] = useState(todayISO);
  const [visibleMonth, setVisibleMonth] = useState(() =>
    parseLocalDate(todayISO())
  );
  const [showCalendar, setShowCalendar] = useState(false);

  const { historyByDate, isMonthLoading, modifiers } =
    useMoodHistory(visibleMonth);

  const didSelectDateRef = useRef(false);

  const [state, setState] = useState<TodayState>({
    status: "not_computed",
    reason: "No prediction for this date",
  });

  /* ───────── Sync selected day ───────── */

  useEffect(() => {
    const day = historyByDate[currentDate];

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
  }, [currentDate, historyByDate]);

  /* ───────── Sync calendar month after date change ───────── */

  useEffect(() => {
    if (!didSelectDateRef.current) return;
    const d = parseLocalDate(currentDate);
    setVisibleMonth(new Date(d.getFullYear(), d.getMonth(), 1));
    didSelectDateRef.current = false;
  }, [currentDate]);

  /* ───────── Derived UI ───────── */

  const isDayPending =
    isMonthLoading && !historyByDate[currentDate];

  let emoji = "🙂";
  let explanationBlock: JSX.Element | null = null;
  let moodText: JSX.Element | null = null;

  if (state.status === "not_computed") {
    explanationBlock = (
      <p className="text-center text-sm text-gray-600">
        {state.reason}
      </p>
    );
  }

  if (state.status === "error") {
    explanationBlock = (
      <p className="text-center text-sm text-red-600">
        {state.message}
      </p>
    );
  }

  if (state.status === "ok") {
    const { predicted_mood, confidence } = state;

    if (predicted_mood <= 2) emoji = "☹️";
    else if (predicted_mood < 3) emoji = "😐";
    else if (predicted_mood < 4) emoji = "🙂";
    else emoji = "😊";

    if (confidence === "low") {
      emoji = "⚪️";
      moodText = (
        <p className="text-center text-sm text-gray-400 italic">
          Not enough data to personalize this day
        </p>
      );
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

  /* ───────── Render (IMPORTANT: RETURN JSX) ───────── */

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-md space-y-4">
        <button
          onClick={() => setShowCalendar((v) => !v)}
          className="w-full rounded-lg bg-gray-100 py-2 text-sm font-medium"
        >
          {showCalendar ? "Hide calendar" : "📅 Pick a date"}
        </button>

        {showCalendar && (
          <MoodCalendar
            visibleMonth={visibleMonth}
            currentDate={currentDate}
            modifiers={modifiers}
            isLoading={isMonthLoading}
            onMonthChange={setVisibleMonth}
            onSelect={(date) => {
              didSelectDateRef.current = true;
              setCurrentDate(date);
            }}
          />
        )}

        <div className="flex items-center justify-between">
          <button
            className="px-3 py-1 bg-gray-100 rounded-lg"
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

          <span className="text-sm font-medium">
            {formatDate(currentDate)}
          </span>

          <button
            className="px-3 py-1 bg-gray-100 rounded-lg"
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

        <div className="flex flex-col items-center space-y-3">
          {isDayPending ? (
            <>
              <div className="animate-pulse text-7xl">⏳</div>
              <p className="text-sm text-gray-400">Loading mood…</p>
            </>
          ) : (
            <>
              <div className="text-7xl">{emoji}</div>
              {moodText}
            </>
          )}
        </div>

        <h1 className="text-center text-xl font-semibold">
          Mood
        </h1>

        {explanationBlock}
      </div>
    </div>
  );
}
