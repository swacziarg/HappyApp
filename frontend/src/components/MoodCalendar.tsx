// src/components/MoodCalendar.tsx
import { DayPicker } from "react-day-picker";
import "react-day-picker/dist/style.css";
import { parseLocalDate } from "../utils/date";

type Props = {
  visibleMonth: Date;
  currentDate: string;
  modifiers: Record<string, Date[]>;
  isLoading: boolean;
  onMonthChange: (d: Date) => void;
  onSelect: (date: string) => void;
};

export function MoodCalendar({
  visibleMonth,
  currentDate,
  modifiers,
  isLoading,
  onMonthChange,
  onSelect,
}: Props) {
  return (
    <div className="relative">
      {isLoading && (
        <p className="text-center text-xs text-gray-400 mb-2">
          Loading month…
        </p>
      )}

      <DayPicker
        mode="single"
        month={visibleMonth}
        onMonthChange={onMonthChange}
        selected={parseLocalDate(currentDate)}
        onSelect={(d) => d && onSelect(d.toLocaleDateString("en-CA"))}
        modifiers={modifiers}
        modifiersClassNames={{
          low: "bg-red-200",
          medium: "bg-yellow-200",
          high: "bg-green-200",
          lowConfidence: "bg-gray-200 text-gray-400 opacity-60",
          missing: "text-gray-300 opacity-40",
          hasNote: "has-note",
        }}        
        disabled={{ after: new Date() }}
      />

      {isLoading && (
        <div className="absolute inset-0 pointer-events-none bg-white/40 rounded-md" />
      )}
    </div>
  );
}
