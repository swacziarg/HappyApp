// src/api/history.ts
import type { HistoryApiResponse } from "../types/mood";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

export async function fetchHistory(start: string, end: string) {
  const res = await fetch(
    `${API_BASE}/history?start=${start}&end=${end}`
  );
  if (!res.ok) throw new Error("Failed to fetch history");
  return res.json() as Promise<HistoryApiResponse>;
}
