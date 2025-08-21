import React from "react";
import Link from "next/link";

const cards = [
  {
    title: "New Client Assessment",
    desc: "Start a comprehensive assessment for a new client, including detailed questions and visualizations.",
    icon: (
      <svg className="w-10 h-10 text-[#1B365D]" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.564-7.499-1.632z" /></svg>
    ),
    cta: "Start Assessment",
    href: "/assessment",
    primary: true,
    isLink: true,
  },
  {
    title: "Quick Coverage Calculator",
    desc: "Get a fast estimate of life insurance needs with just a few questions.",
    icon: (
      <svg className="w-10 h-10 text-[#1B365D]" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M16.5 6v.75m0 3v.75m0 3v.75m0 3v.75m-9-9v.75m0 3v.75m0 3v.75m0 3v.75M3.75 6.75A2.25 2.25 0 016 4.5h12a2.25 2.25 0 012.25 2.25v12A2.25 2.25 0 0118 20.25H6A2.25 2.25 0 013.75 18V6.75z" /></svg>
    ),
    cta: "Calculate",
    href: "/quick-calculator",
    primary: false,
    isLink: true,
  },
  {
    title: "Client Portfolio Assessment",
    desc: "Upload client files and analyze life insurance in the context of their full portfolio.",
    icon: (
      <svg className="w-10 h-10 text-[#1B365D]" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 3v1.5A2.25 2.25 0 005.25 6.75h13.5A2.25 2.25 0 0021 4.5V3M3 21v-1.5A2.25 2.25 0 015.25 17.25h13.5A2.25 2.25 0 0021 19.5V21M3 7.5h18M3 12h18M3 16.5h18" /></svg>
    ),
    cta: "Upload & Analyze",
    href: "/portfolio-assessment",
    primary: true,
    isLink: true,
  },
  {
    title: "Robo-Advisor Chatbot",
    desc: "Ask questions, upload files, and get AI-powered financial insights.",
    icon: (
      <svg className="w-10 h-10 text-[#1B365D]" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M7.5 10.5h9m-9 3h6m-6 3h3m-6-9h12A2.25 2.25 0 0121 7.5v9A2.25 2.25 0 0118.75 19.5H5.25A2.25 2.25 0 013 16.5v-9A2.25 2.25 0 015.25 4.5h13.5A2.25 2.25 0 0121 7.5v9A2.25 2.25 0 0118.75 19.5H5.25A2.25 2.25 0 013 16.5v-9z" /></svg>
    ),
    cta: "Ask Question",
    href: "/robo-advisor",
    primary: false,
    isLink: true,
  },
];

function Card({ title, desc, icon, cta, href, primary, isLink }: any) {
  const Button = isLink ? Link : "a";
  return (
    <div className="flex flex-col items-start bg-white rounded-2xl shadow-lg p-8 min-w-[260px] max-w-xs flex-1 transition-transform hover:-translate-y-1 hover:shadow-2xl border border-gray-100">
      <div className="mb-6">{icon}</div>
      <h3 className="text-xl font-extrabold text-[#1B365D] mb-2" style={{ fontFamily: 'Inter, sans-serif' }}>{title}</h3>
      <p className="text-gray-500 text-base mb-6 flex-1" style={{ fontFamily: 'Inter, sans-serif' }}>{desc}</p>
      <Button href={href} className={`mt-auto w-full px-0 py-3 rounded-lg font-bold text-base text-center ${primary ? "bg-[#1B365D] text-white hover:bg-blue-900" : "bg-white border border-[#1B365D] text-[#1B365D] hover:bg-blue-50"}`}>{cta}</Button>
    </div>
  );
}

export default function Dashboard() {
  return (
    <>
      {/* Title left-aligned, no underline */}
      <div className="w-full flex flex-col items-start px-12">
        <h1 className="text-4xl font-extrabold text-[#1B365D] mt-6 mb-8" style={{ fontFamily: 'Inter, sans-serif' }}>
          Life Insurance Robo-Advisor
        </h1>
      </div>
      {/* Card grid */}
      <div className="w-full px-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-14">
        {cards.map((card, i) => <Card key={i} {...card} />)}
      </div>
      {/* Panels below cards */}
      <div className="w-full px-12 grid grid-cols-1 md:grid-cols-2 gap-8 pb-12">
        <div className="bg-[#F8F9FA] rounded-2xl shadow p-8 min-h-[440px] flex flex-col">
          <h2 className="text-2xl font-bold text-[#1B365D] mb-6" style={{ fontFamily: 'Inter, sans-serif' }}>Recent Client Activity</h2>
          <ul className="flex-1 space-y-5">
            <li className="flex items-center gap-3 text-gray-700"><span className="bg-gray-100 rounded-full p-3"><svg className="w-6 h-6 text-[#1B365D]" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.564-7.499-1.632z" /></svg></span><span className="font-semibold">Erana Milson</span> <span className="ml-auto text-sm text-gray-400">24 ago</span></li>
            <li className="flex items-center gap-3 text-gray-700"><span className="bg-gray-100 rounded-full p-3"><svg className="w-6 h-6 text-[#1B365D]" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.564-7.499-1.632z" /></svg></span><span className="font-semibold">Jawso Smith</span> <span className="ml-auto text-sm text-gray-400">14 ago</span></li>
            <li className="flex items-center gap-3 text-gray-700"><span className="bg-gray-100 rounded-full p-3"><svg className="w-6 h-6 text-[#1B365D]" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.564-7.499-1.632z" /></svg></span><span className="font-semibold">Sarsh Johnson</span> <span className="ml-auto text-sm text-gray-400">14 ago</span></li>
          </ul>
        </div>
        <div className="bg-[#F8F9FA] rounded-2xl shadow p-8 min-h-[440px] flex flex-col">
          <h2 className="text-2xl font-bold text-[#1B365D] mb-6" style={{ fontFamily: 'Inter, sans-serif' }}>AI Chatbot</h2>
          {/* Chatbot UI */}
          <div className="flex-1 flex flex-col justify-end">
            <div className="flex-1 overflow-y-auto mb-4 space-y-2" style={{ maxHeight: 220 }}>
              {/* Example chat bubbles */}
              <div className="self-start bg-white rounded-lg px-4 py-2 shadow text-gray-800 max-w-[80%]">Hello! How can I help you today?</div>
              <div className="self-end bg-[#1B365D] text-white rounded-lg px-4 py-2 shadow max-w-[80%]">What is Termvest+?</div>
              <div className="self-start bg-white rounded-lg px-4 py-2 shadow text-gray-800 max-w-[80%]">Termvest+ is our innovative life insurance product. Would you like to learn more?</div>
            </div>
            <form className="flex items-center gap-2 mt-2">
              <input type="text" className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#1B365D]" placeholder="Type your message..." disabled />
              <button type="submit" className="bg-[#1B365D] text-white rounded-lg px-4 py-2 font-semibold shadow hover:bg-blue-900" disabled>Send</button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
