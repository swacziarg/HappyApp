export default function About() {
    return (
      <main className="min-h-screen bg-gray-100 flex items-center justify-center px-4">
        <section className="max-w-xl bg-white rounded-2xl shadow-md p-8 space-y-6">
          <h1 className="text-3xl font-semibold text-gray-900">
            About This Project
          </h1>
  
          <p className="text-gray-700 leading-relaxed">
            This project began by trying to find out whether the data we collect
            every day could help explain how a day actually feels. Using sleep, heart
            rate variability, stress, and activity data from a Garmin device,
            the app produces a daily mood score on a scale from 1-5, with a short explanation of what likely influenced it.
          </p>
  
          <p className="text-gray-700 leading-relaxed">
            Recovery, accumulated stress, and activity patterns all shape how a day tends
            to feel. The goal is to offer gentle signals that help put each day into
            perspective.
          </p>
  
          <p className="text-gray-700 leading-relaxed">
            The system is intentionally simple and interpretable. Each day is
            compared against your own recent patterns instead of population
            averages. Changes from your normal sleep, recovery, or stress levels
            matter more than raw numbers. Sleep and recovery typically have the
            strongest influence, while activity and stress add supporting context.
          </p>
  
          <p className="text-gray-700 leading-relaxed">
            Behind the scenes, the app processes historical Garmin data, organizes
            it into a structured database, extracts daily features, and combines
            them using a clear rules-based approach. The result is a
            wellbeing score paired with an explanation and a
            confidence level based on data availability.
          </p>
  
          <p className="text-gray-600 text-sm leading-relaxed">
            The app is built and maintained as a personal project by me, a Computer
            Science junior at UW–Madison, with a focus on data engineering,
            backend systems, and transparent, human-centered reasoning grounded
            in real signals.
          </p>
        </section>
      </main>
    );
  }
  