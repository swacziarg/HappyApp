import { Link } from "react-router-dom";
import { GarminUpload } from "../components/GarminUpload";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-emerald-50 flex items-center justify-center px-4">
      <div className="max-w-xl w-full text-center">
        <div className="rounded-3xl bg-white/80 backdrop-blur p-8 shadow-xl space-y-6">
          <div className="text-6xl">🌤️</div>

          <h1 className="text-4xl font-bold text-gray-900 tracking-tight">
            Understand your mood
          </h1>

          <p className="text-gray-600 text-lg leading-relaxed">
            A data-driven way to reflect on how you’ve been feeling,
            one day at a time.
          </p>

          <div className="pt-4">
            <Link
              to="/mood"
              className="
                inline-flex items-center justify-center
                rounded-xl bg-indigo-600 px-6 py-3
                text-white font-medium
                shadow-md
                hover:bg-indigo-700
                focus:outline-none focus:ring-2 focus:ring-indigo-400
                transition
              "
            >
              View today’s mood →
            </Link>
          </div>

          {/* 👇 Garmin upload */}
          <GarminUpload />
        </div>
      </div>
    </div>
  );
}
