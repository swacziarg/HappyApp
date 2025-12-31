export default function Today() {
  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-md">
        {/* Mood */}
        <div className="flex justify-center mb-4">
          <span className="text-7xl">🙂</span>
        </div>

        {/* Title */}
        <h1 className="text-center text-xl font-semibold text-gray-900">
          Mood Today
        </h1>

        {/* Explanation */}
        <p className="mt-3 text-center text-sm text-gray-600 leading-relaxed">
          This is a placeholder explanation that will later describe
          why today’s mood was predicted this way.
        </p>

        {/* Divider */}
        <div className="my-5 h-px bg-gray-200" />

        {/* Confidence */}
        <p className="text-center text-sm text-gray-500">
          Confidence: <span className="font-medium text-gray-700">Medium</span>
        </p>
      </div>
    </div>
  )
}
