"use client";
import { useState } from "react";
import { fetchProductFAQ } from "@/utils/api";

const SUGGESTED_QUESTIONS = [
  "What is term life insurance?",
  "What is IUL?",
  "How is my coverage calculated?",
  "Why do I need life insurance?",
  "What is cash value?",
];

export default function Chatbot({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [messages, setMessages] = useState<{ sender: string; text: string }[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async (msg?: string) => {
    const question = msg ?? input;
    if (!question.trim()) return;
    setMessages((msgs) => [...msgs, { sender: "user", text: question }]);
    setLoading(true);
    try {
      const res = await fetchProductFAQ(question);
      setMessages((msgs) => [
        ...msgs,
        { sender: "bot", text: res.answer },
      ]);
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        { sender: "bot", text: "Sorry, I couldn't get an answer right now." },
      ]);
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 flex items-end justify-end z-50">
      <div className="bg-white w-full max-w-sm rounded-t-lg shadow-lg p-4 flex flex-col h-[60vh]">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-lg font-bold text-blue-900">Ask a Question</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">&times;</button>
        </div>
        <div className="flex-1 overflow-y-auto space-y-2 mb-2">
          {messages.length === 0 && (
            <div className="text-gray-400 text-center mt-8">Ask about term, IUL, cash value, or why life insurance is important.</div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={msg.sender === "user" ? "text-right" : "text-left"}>
              <span className={msg.sender === "user" ? "inline-block bg-blue-100 text-blue-900 rounded px-3 py-1" : "inline-block bg-green-100 text-green-900 rounded px-3 py-1"}>
                {msg.text}
              </span>
            </div>
          ))}
        </div>
        <div className="mb-2 flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              className="bg-gray-100 hover:bg-blue-100 text-blue-900 rounded px-2 py-1 text-xs border border-blue-200"
              onClick={() => sendMessage(q)}
              disabled={loading}
            >
              {q}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            className="flex-1 border rounded px-2 py-1 focus:outline-none focus:ring"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") sendMessage(); }}
            placeholder="Type your question..."
            disabled={loading}
          />
          <button
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-1 rounded"
            onClick={() => sendMessage()}
            disabled={loading}
          >
            {loading ? "..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
} 