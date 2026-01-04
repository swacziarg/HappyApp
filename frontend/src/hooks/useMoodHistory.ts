// src/hooks/useMoodHistory.ts
import { useEffect, useMemo, useRef, useState } from "react";
import { fetchHistory } from "../api/history";
import type { HistoryDay } from "../types/mood";
import { monthBoundsFromDate, parseLocalDate, moodBucket } from "../utils/date";

export function useMoodHistory(visibleMonth: Date) {
  const [historyByDate, setHistoryByDate] = useState<
    Record<string, HistoryDay>
  >({});
  const [isMonthLoading, setIsMonthLoading] = useState(false);

  const loadedMonthsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    const key = `${visibleMonth.getFullYear()}-${visibleMonth.getMonth()}`;
    if (loadedMonthsRef.current.has(key)) return;

    loadedMonthsRef.current.add(key);
    setIsMonthLoading(true);

    const { start, end } = monthBoundsFromDate(visibleMonth);

    fetchHistory(start, end)
      .then((d) => {
        setHistoryByDate((prev) => {
          const next = { ...prev };
          for (const day of d.days ?? []) {
            next[day.date] = day;
          }
          return next;
        });
      })
      .finally(() => setIsMonthLoading(false));
  }, [visibleMonth]);

  const historyForVisibleMonth = useMemo(() => {
    const m = visibleMonth.getMonth();
    const y = visibleMonth.getFullYear();

    return Object.values(historyByDate).filter((d) => {
      const dt = parseLocalDate(d.date);
      return dt.getMonth() === m && dt.getFullYear() === y;
    });
  }, [historyByDate, visibleMonth]);

  const modifiers = useMemo(() => {
    return {
      low: historyForVisibleMonth
        .filter(
          (d) =>
            d.status === "available" &&
            d.confidence !== "low" &&
            moodBucket(d.predicted_mood) === "low"
        )
        .map((d) => parseLocalDate(d.date)),
      medium: historyForVisibleMonth
        .filter(
          (d) =>
            d.status === "available" &&
            d.confidence !== "low" &&
            moodBucket(d.predicted_mood) === "medium"
        )
        .map((d) => parseLocalDate(d.date)),
      high: historyForVisibleMonth
        .filter(
          (d) =>
            d.status === "available" &&
            d.confidence !== "low" &&
            moodBucket(d.predicted_mood) === "high"
        )
        .map((d) => parseLocalDate(d.date)),
      lowConfidence: historyForVisibleMonth
        .filter((d) => d.status === "available" && d.confidence === "low")
        .map((d) => parseLocalDate(d.date)),
      missing: historyForVisibleMonth
        .filter((d) => d.status === "missing")
        .map((d) => parseLocalDate(d.date)),
    };
  }, [historyForVisibleMonth]);

  return {
    historyByDate,
    isMonthLoading,
    modifiers,
  };
}
