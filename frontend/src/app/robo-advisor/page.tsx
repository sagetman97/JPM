"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  files?: File[];
  qualityScore?: number;
  routingDecision?: any;
  disclaimers?: string[];
}

interface ChatResponse {
  content: string;
  quality_score: number;
  routing_decision: any;
  disclaimers: string[];
  session_id: string;
}

export default function RoboAdvisorPage() {
  const [inputValue, setInputValue] = useState("");
  const [inputRows, setInputRows] = useState(1);
  const [isDragOver, setIsDragOver] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();
    
    // Add welcome message
    setMessages([{
      id: 'welcome',
      type: 'assistant',
      content: 'Hello! I\'m your AI financial advisor. I can help you with life insurance questions, coverage calculations, and portfolio analysis. What would you like to know?',
      timestamp: new Date()
    }]);

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(`ws://localhost:8000/chatbot/ws/chat/${sessionId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Attempt to reconnect
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      setIsConnected(false);
    }
  };

  const handleWebSocketMessage = (data: any) => {
    if (data.type === 'chat_response') {
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'assistant',
        content: data.content,
        timestamp: new Date(),
        qualityScore: data.quality_score,
        routingDecision: data.routing_decision,
        disclaimers: data.disclaimers
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    } else if (data.type === 'error') {
      const errorMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        type: 'assistant',
        content: `Error: ${data.content}`,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
      setIsTyping(false);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || !isConnected) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Send message through WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'chat_message',
        content: inputValue,
        session_id: sessionId,
        timestamp: new Date().toISOString()
      }));
    } else {
      // Fallback to HTTP API if WebSocket is not available
      try {
        const response = await fetch('http://localhost:8000/chatbot/api/chat/process', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: inputValue,
            session_id: sessionId
          })
        });

        if (response.ok) {
          const data: ChatResponse = await response.json();
          const assistantMessage: ChatMessage = {
            id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type: 'assistant',
            content: data.content,
            timestamp: new Date(),
            qualityScore: data.quality_score,
            routingDecision: data.routing_decision,
            disclaimers: data.disclaimers
          };
          
          setMessages(prev => [...prev, assistantMessage]);
        } else {
          throw new Error('Failed to send message');
        }
      } catch (error) {
        console.error('Error sending message:', error);
        const errorMessage: ChatMessage = {
          id: `error_${Date.now()}`,
          type: 'assistant',
          content: 'Sorry, I encountered an error processing your message. Please try again.',
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, errorMessage]);
      }
      
      setIsTyping(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setInputValue(value);
    
    // Calculate rows based on content (min 1, max 8)
    const lines = value.split('\n').length;
    const newRows = Math.min(Math.max(lines, 1), 8);
    setInputRows(newRows);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      console.log('Files uploaded:', files);
      // TODO: Implement file upload to backend
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      console.log('Files dropped:', files);
      // TODO: Implement file drop to backend
    }
  };

  return (
    <>
      {/* Title left-aligned, no underline */}
      <div className="w-full flex flex-col items-start px-12">
        <h1 className="text-4xl font-extrabold text-[#1B365D] mt-6 mb-6" style={{ fontFamily: 'Inter, sans-serif' }}>
          AI Robo-Advisor
        </h1>
        <p className="text-xl text-gray-600 mb-8" style={{ fontFamily: 'Inter, sans-serif' }}>
          Get personalized financial advice, portfolio analysis, and life insurance recommendations through AI-powered conversations
        </p>
      </div>

      {/* Main Chatbot Interface */}
      <div className="w-full px-12 mb-8">
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 h-[1200px] flex flex-col">
          {/* Chat Header */}
          <div className="bg-gradient-to-r from-[#1B365D] to-[#2C5282] text-white p-6 rounded-t-2xl">
            <div className="flex items-center space-x-4">
              <div className="bg-white bg-opacity-20 rounded-full p-3 backdrop-blur-sm">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold">Life Insurance AI Advisor</h3>
                <p className="text-base opacity-95 mt-1">
                  Your AI assistant for life insurance education, calculations, and portfolio integration
                </p>
              </div>
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
                <span className="text-sm opacity-90">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>

          {/* Messages Area - Now Much Taller */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-gray-50 to-white">
            {/* Messages */}
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl px-5 py-4 ${
                  message.type === 'user' 
                    ? 'bg-[#1B365D] text-white' 
                    : 'bg-white shadow-sm border border-gray-100'
                }`}>
                  <div className="flex items-start space-x-4">
                    {message.type === 'assistant' && (
                      <div className="bg-gradient-to-br from-[#1B365D] to-[#2C5282] rounded-full p-3 flex-shrink-0 shadow-lg">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                      </div>
                    )}
                    <div className="flex-1">
                      <div className="text-sm leading-relaxed whitespace-pre-wrap">
                        {message.content}
                      </div>
                      {message.disclaimers && message.disclaimers.length > 0 && (
                        <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <div className="text-xs text-yellow-800 font-medium mb-1">Important Disclaimers:</div>
                          {message.disclaimers.map((disclaimer, index) => (
                            <div key={index} className="text-xs text-yellow-700">• {disclaimer}</div>
                          ))}
                        </div>
                      )}
                      {message.qualityScore && (
                        <div className="mt-2 text-xs text-gray-500">
                          Response Quality: {(message.qualityScore * 100).toFixed(0)}%
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex justify-start">
                <div className="max-w-[85%] rounded-2xl px-5 py-4 bg-white shadow-sm border border-gray-100">
                  <div className="flex items-center space-x-2">
                    <div className="bg-gradient-to-br from-[#1B365D] to-[#2C5282] rounded-full p-3 flex-shrink-0 shadow-lg">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-6 border-t border-gray-200 bg-white rounded-b-2xl">
            {/* File Upload Button - Inside Input Box */}
            <div className="relative">
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2 z-10">
                <label htmlFor="file-upload" className="cursor-pointer">
                  <div className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200">
                    <svg className="w-5 h-5 text-gray-500 hover:text-gray-700" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                    </svg>
                  </div>
                </label>
                <input
                  id="file-upload"
                  type="file"
                  multiple
                  accept=".pdf,.csv,.xlsx,.xls,.docx,.doc,.txt"
                  className="hidden"
                  onChange={handleFileUpload}
                />
              </div>
              
              <textarea
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                rows={inputRows}
                maxLength={2000}
                placeholder="Ask anything about life insurance, financial planning, or portfolio analysis..."
                className="w-full pl-12 pr-16 py-3 border border-gray-300 rounded-xl focus:outline-none focus:border-[#1B365D] hover:border-gray-400 transition-colors duration-200 resize-none text-black placeholder-gray-500 caret-[#1B365D]"
                style={{ minHeight: '48px', maxHeight: '300px' }}
              />
              
              {/* Send Button */}
              <button
                onClick={sendMessage}
                className={`absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-lg transition-all duration-200 ${
                  inputValue.trim() && isConnected
                    ? 'bg-[#1B365D] text-white hover:bg-[#2C5282] shadow-md' 
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
                disabled={!inputValue.trim() || !isConnected}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
            
            {/* Quick Action Buttons - Enhanced Design */}
            <div className="mt-4 flex flex-wrap gap-3">
              <button 
                className="text-sm bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 px-4 py-2 rounded-xl hover:from-blue-100 hover:to-blue-200 border border-blue-200 transition-all duration-200 font-medium shadow-sm"
                onClick={() => setInputValue("I need help calculating my life insurance needs")}
              >
                💰 Coverage Calculator
              </button>
              <button 
                className="text-sm bg-gradient-to-r from-green-50 to-green-100 text-green-700 px-4 py-2 rounded-xl hover:from-green-100 hover:to-green-200 border border-green-200 transition-all duration-200 font-medium shadow-sm"
                onClick={() => setInputValue("How does life insurance fit into my investment portfolio?")}
              >
                📊 Portfolio Integration
              </button>
              <button 
                className="text-sm bg-gradient-to-r from-purple-50 to-purple-100 text-purple-700 px-4 py-2 rounded-xl hover:from-purple-100 hover:to-purple-200 border border-purple-200 transition-all duration-200 font-medium shadow-sm"
                onClick={() => setInputValue("Explain the difference between term and whole life insurance")}
              >
                📚 Product Education
              </button>
              <button 
                className="text-sm bg-gradient-to-r from-orange-50 to-orange-100 text-orange-700 px-4 py-2 rounded-xl hover:from-orange-100 hover:to-orange-200 border border-orange-200 transition-all duration-200 font-medium shadow-sm"
                onClick={() => setInputValue("I need a comprehensive client assessment")}
              >
                👥 Client Assessment
              </button>
            </div>
            
            {/* Status Indicator - Enhanced */}
            <div className="mt-4 text-center">
              <div className={`inline-flex items-center space-x-3 text-sm px-4 py-2 rounded-full border transition-all duration-200 ${
                isConnected 
                  ? 'text-green-700 bg-green-50 border-green-200' 
                  : 'text-red-700 bg-red-50 border-red-200'
              }`}>
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="font-medium">
                  {isConnected ? 'Connected to AI Advisor' : 'Connecting to AI Advisor...'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Information Cards - Enhanced Design */}
      <div className="w-full px-12 grid grid-cols-1 md:grid-cols-3 gap-8 pb-12">
        <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
          <div className="flex items-center space-x-4 mb-6">
            <div className="bg-gradient-to-br from-blue-100 to-blue-200 rounded-full p-4">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-800">AI-Powered Insights</h3>
          </div>
          <p className="text-gray-600 leading-relaxed">
            Get intelligent, contextual responses to complex financial questions using advanced AI and comprehensive knowledge bases. 
            Our system understands context and provides personalized recommendations.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
          <div className="flex items-center space-x-4 mb-6">
            <div className="bg-gradient-to-br from-green-100 to-green-200 rounded-full p-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-800">Compliance & Safety</h3>
          </div>
          <p className="text-gray-600 leading-relaxed">
            Built-in compliance guardrails and legal disclaimers ensure all responses meet regulatory requirements for financial advisors. 
            Your clients get accurate, compliant information every time.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
          <div className="flex items-center space-x-4 mb-6">
            <div className="bg-gradient-to-br from-purple-100 to-purple-200 rounded-full p-4">
              <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-800">Advanced RAG & Search</h3>
          </div>
          <p className="text-gray-600 leading-relaxed">
            Combines internal knowledge bases with external search capabilities to provide comprehensive, up-to-date information. 
            When our documentation falls short, we intelligently search external sources and evaluate response quality.
          </p>
        </div>
      </div>
    </>
  );
} 