// src/utils/date.ts

export function todayISO() {
    return new Date().toLocaleDateString("en-CA");
  }
  
  export function parseLocalDate(date: string) {
    const [y, m, d] = date.split("-").map(Number);
    return new Date(y, m - 1, d);
  }
  
  export function formatDate(date: string) {
    return parseLocalDate(date).toLocaleDateString(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  }
  
  export function monthBoundsFromDate(d: Date) {
    return {
      start: new Date(d.getFullYear(), d.getMonth(), 1).toLocaleDateString("en-CA"),
      end: new Date(d.getFullYear(), d.getMonth() + 1, 0).toLocaleDateString(
        "en-CA"
      ),
    };
  }
  
  export function moodBucket(mood: number) {
    if (mood <= 2) return "low";
    if (mood < 4) return "medium";
    return "high";
  }
  