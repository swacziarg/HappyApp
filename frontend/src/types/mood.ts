// src/types/mood.ts

export type Confidence = "low" | "medium" | "high";

export type TodayOk = {
  status: "ok";
  date: string;
  predicted_mood: number;
  confidence: Confidence;
  explanation: string[];
};

export type TodayState =
  | { status: "error"; message: string }
  | { status: "not_computed"; reason: string }
  | TodayOk;

export type HistoryDay = {
  date: string;
  predicted_mood: number;
  confidence: Confidence;
  explanation: string[];
  status: "available" | "missing";
};

export type HistoryApiResponse = {
  start: string;
  end: string;
  days: HistoryDay[];
};
