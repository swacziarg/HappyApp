import { useEffect, useRef, useState, type JSX, useMemo } from "react";
import { MoodCalendar } from "../components/MoodCalendar";
import { useMoodHistory } from "../hooks/useMoodHistory";
import { useMoodCheckins } from "../hooks/useMoodCheckin";
import type { TodayState } from "../types/mood";
import {
  todayISO,
  parseLocalDate,
  formatDate,
} from "../utils/date";
import { API_BASE_URL } from "../api/config";

const MOOD_EMOJIS = ["😞", "🙁", "😐", "🙂", "😊"];

export default function Today(): JSX.Element {
  const [currentDate, setCurrentDate] = useState(todayISO);
  const [visibleMonth, setVisibleMonth] = useState(() =>
    parseLocalDate(todayISO())
  );
  const [showCalendar, setShowCalendar] = useState(false);

  /* ───────── History (predictions) ───────── */

  const { historyByDate, isMonthLoading, modifiers } =
    useMoodHistory(visibleMonth);

  const didSelectDateRef = useRef(false);

  const [state, setState] = useState<TodayState>({
    status: "not_computed",
    reason: "No prediction for this date",
  });

  /* ───────── Check-ins (monthly cached) ───────── */

  const {
    byDate: checkinsByDate,
    isLoading: isCheckinsLoading,
    setByDate: setCheckinsByDate,
  } = useMoodCheckins(visibleMonth);

  const moodCheckin = checkinsByDate[currentDate] ?? null;

  const [checkinMood, setCheckinMood] = useState<number | null>(null);
  const [checkinNote, setCheckinNote] = useState("");
  const [isEditingCheckin, setIsEditingCheckin] = useState(true);
  const [isSavingCheckin, setIsSavingCheckin] = useState(false);

  /* ───────── Calendar note markers (derived, no fetch) ───────── */

  const noteDays = useMemo(() => {
    return Object.values(checkinsByDate)
      .filter((c) => {
        if (!c.note || c.note.trim().length === 0) return false;
        const d = parseLocalDate(c.date);
        return (
          d.getMonth() === visibleMonth.getMonth() &&
          d.getFullYear() === visibleMonth.getFullYear()
        );
      })
      .map((c) => parseLocalDate(c.date));
  }, [checkinsByDate, visibleMonth]);

  /* ───────── Sync selected day (prediction) ───────── */

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

  /* ───────── Sync selected day (check-in) ───────── */

  useEffect(() => {
    if (isCheckinsLoading) return;

    const isToday = currentDate === todayISO();

    if (moodCheckin) {
      setCheckinMood(moodCheckin.mood);
      setCheckinNote(moodCheckin.note ?? "");
      setIsEditingCheckin(false);
      return;
    }

    if (isToday) {
      setCheckinMood(null);
      setCheckinNote("");
      setIsEditingCheckin(true);
    } else {
      setCheckinMood(null);
      setCheckinNote("");
      setIsEditingCheckin(false);
    }
  }, [moodCheckin, isCheckinsLoading, currentDate]);

  /* ───────── Sync calendar month after date change ───────── */

  useEffect(() => {
    if (!didSelectDateRef.current) return;

    const d = parseLocalDate(currentDate);
    setVisibleMonth(new Date(d.getFullYear(), d.getMonth(), 1));
    didSelectDateRef.current = false;
  }, [currentDate]);

  /* ───────── Submit mood check-in ───────── */

  async function submitCheckin() {
    if (!checkinMood) return;

    setIsSavingCheckin(true);

    try {
      await fetch(`${API_BASE_URL}/mood`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date: currentDate,
          mood: checkinMood,
          note: checkinNote || null,
        }),
      });

      // optimistic cache update
      setCheckinsByDate((prev) => ({
        ...prev,
        [currentDate]: {
          date: currentDate,
          mood: checkinMood,
          note: checkinNote || null,
        },
      }));

      setIsEditingCheckin(false);
    } finally {
      setIsSavingCheckin(false);
    }
  }

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

  /* ───────── Render ───────── */

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
            modifiers={{
              ...modifiers,
              hasNote: noteDays,
            }}
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

        {/* ───────── Mood check-in ───────── */}

        <div className="space-y-3">
          {isEditingCheckin ? (
            <>
              <div className="flex justify-center gap-2 text-2xl">
                {MOOD_EMOJIS.map((e, i) => {
                  const value = i + 1;
                  const selected = checkinMood === value;

                  return (
                    <button
                      key={value}
                      onClick={() => setCheckinMood(value)}
                      className={`transition ${
                        selected ? "scale-125" : "opacity-50"
                      }`}
                    >
                      {e}
                    </button>
                  );
                })}
              </div>

              <textarea
                value={checkinNote}
                onChange={(e) => setCheckinNote(e.target.value)}
                placeholder="Add a note about today…"
                className="w-full rounded-lg border p-2 text-sm"
                rows={3}
              />

              <button
                disabled={!checkinMood || isSavingCheckin}
                onClick={submitCheckin}
                className="w-full rounded-lg bg-black py-2 text-sm text-white disabled:opacity-50"
              >
                {isSavingCheckin ? "Saving…" : "Save mood"}
              </button>
            </>
          ) : (
            <>
              <div className="flex justify-center text-3xl">
                {checkinMood ? MOOD_EMOJIS[checkinMood - 1] : null}
              </div>

              {checkinNote && (
                <p className="text-center text-sm text-gray-600 whitespace-pre-wrap">
                  {checkinNote}
                </p>
              )}

              {currentDate === todayISO() && (
                <button
                  onClick={() => setIsEditingCheckin(true)}
                  className="mx-auto block text-xs text-gray-500 underline"
                >
                  Edit
                </button>
              )}
            </>
          )}
        </div>

        {explanationBlock}
      </div>
    </div>
  );
}
