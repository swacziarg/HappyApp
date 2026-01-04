import { useEffect, useRef, useState } from "react";
import { monthBoundsFromDate } from "../utils/date";

export type MoodCheckin = {
  date: string;
  mood: number;
  note: string | null;
};

const API_BASE = "http://localhost:8000";

export function useMoodCheckins(visibleMonth: Date) {
  const [byDate, setByDate] = useState<Record<string, MoodCheckin>>({});
  const [isLoading, setIsLoading] = useState(false);

  const loadedMonthsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    const key = `${visibleMonth.getFullYear()}-${visibleMonth.getMonth()}`;
    if (loadedMonthsRef.current.has(key)) return;

    loadedMonthsRef.current.add(key);
    setIsLoading(true);

    const { start, end } = monthBoundsFromDate(visibleMonth);

    fetch(`${API_BASE}/mood?start=${start}&end=${end}`)
      .then((r) => r.json())
      .then((json) => {
        setByDate((prev) => {
          const next = { ...prev };
          for (const day of json.days ?? []) {
            if (day.status === "available") {
              next[day.date] = {
                date: day.date,
                mood: day.mood,
                note: day.note,
              };
            }
          }
          return next;
        });
      })
      .finally(() => setIsLoading(false));
  }, [visibleMonth]);

  return { byDate, isLoading, setByDate };
}
