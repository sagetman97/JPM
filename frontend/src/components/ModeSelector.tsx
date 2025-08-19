"use client";

export default function ModeSelector({ mode, setMode }: { mode: string; setMode: (m: string) => void }) {
  return (
    <div className="flex gap-4 mb-6 justify-center">
      <button
        className={`px-4 py-2 rounded font-semibold border transition ${mode === "client" ? "bg-blue-900 text-white" : "bg-white text-blue-900 border-blue-900"}`}
        onClick={() => setMode("client")}
      >
        Client Mode
      </button>
      <button
        className={`px-4 py-2 rounded font-semibold border transition ${mode === "advisor" ? "bg-green-700 text-white" : "bg-white text-green-700 border-green-700"}`}
        onClick={() => setMode("advisor")}
      >
        Advisor Mode
      </button>
    </div>
  );
} 