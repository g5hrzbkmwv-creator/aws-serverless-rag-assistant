import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, Upload, Sparkles, CheckCircle, Loader2 } from 'lucide-react';

export default function RAGAssistantUI() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: 'Hello! I am your enterprise-level RAG knowledge assistant. How can I assist you?',
      sources: 0
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const chatEndRef = useRef(null);

  // 自動捲動到最新訊息
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 1. 發送問題至 API Gateway
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userQuery = input;
    setInput('');
    
    // 新增使用者訊息
    const userMsg = { id: Date.now(), sender: 'user', text: userQuery };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      // 🔗 換成你的 API Gateway Invoke URL
      const response = await fetch(`${import.meta.env.VITE_API_GATEWAY_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userQuery }),
      });

      const data = await response.json();
      
      const botMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        text: data.answer || 'Sorry, the response format was incorrect.',
        sources: data.sources_used || 0
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, sender: 'bot', text: '⚠️ A connection error has occurred. Please try again later.', sources: 0 }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // 2. 模擬文件上傳至 S3
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    // 💡 可串接 S3 Presigned URL 或 API Gateway 觸發上傳
    setTimeout(() => {
      setUploading(false);
      alert(`文件 "${file.name}" 上傳成功！系統背景正在進行向量化處理...`);
    }, 2000);
  };

  return (
    <div className="flex h-screen bg-slate-900 text-slate-100 font-sans">
      {/* 側邊欄 - 檔案管理 */}
      <aside className="w-72 bg-slate-950 border-r border-slate-800 p-4 flex flex-col justify-between hidden md:flex">
        <div>
          <div className="flex items-center gap-2 mb-6 px-2">
            <Sparkles className="w-6 h-6 text-indigo-400" />
            <h1 className="font-bold text-lg tracking-wide">Enterprise RAG</h1>
          </div>
        {/* 
          <div className="mb-4">
            <label className="flex items-center justify-center gap-2 w-full p-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl cursor-pointer transition shadow-lg shadow-indigo-600/20 font-medium">
              {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              <span>{uploading ? '向量化處理中...' : '上傳知識庫文件'}</span>
              <input type="file" className="hidden" onChange={handleFileUpload} accept=".txt,.pdf,.md" />
            </label>
          </div>

          <div className="space-y-2 mt-6">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-2">知識庫文件狀態</p>
            <div className="flex items-center gap-2 p-2 rounded-lg bg-slate-900/50 text-sm text-slate-300 border border-slate-800">
              <FileText className="w-4 h-4 text-emerald-400" />
              <span className="truncate flex-1">test.txt</span>
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            </div>
          </div>
          */}
        </div>

        <div className="text-xs text-slate-500 px-2">
          Powered by AWS Bedrock (Nova Pro) & S3 Vector Storage
        </div>
      </aside>

      {/* 主聊天區域 */}
      <main className="flex-1 flex flex-col h-full bg-slate-900">
        {/* Header */}
        <header className="h-16 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900/80 backdrop-blur">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
            <h2 className="font-semibold text-slate-200">Serverless RAG Knowledge Assistant</h2>
          </div>
        </header>

        {/* 對話訊息列表 */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-4 max-w-3xl ${msg.sender === 'user' ? 'ml-auto flex-row-reverse' : ''}`}>
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                msg.sender === 'user' ? 'bg-indigo-600' : 'bg-slate-800 border border-slate-700'
              }`}>
                {msg.sender === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5 text-indigo-400" />}
              </div>

              <div className="space-y-2">
                <div className={`p-4 rounded-2xl leading-relaxed text-sm shadow-sm ${
                  msg.sender === 'user' 
                    ? 'bg-indigo-600 text-white rounded-tr-none' 
                    : 'bg-slate-800/80 text-slate-200 border border-slate-700/60 rounded-tl-none'
                }`}>
                  {msg.text}
                </div>

                {/* 展示 RAG 引用資訊 */}
                {msg.sender === 'bot' && msg.sources > 0 && (
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-950/50 border border-indigo-800/40 text-xs text-indigo-300">
                    <FileText className="w-3 h-3 paper-file" />
                    <span>I have referenced {msg.sources} internal knowledge base fragments.</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-4 max-w-3xl">
              <div className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center">
                <Bot className="w-5 h-5 text-indigo-400 animate-bounce" />
              </div>
              <div className="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/60 text-slate-400 text-sm flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                Retrieving data from the S3 vector database and generating an answer...
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* 輸入框 */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/50 form-bg">
          <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask any questions about the knowledge base files..."
              className="w-full bg-slate-800/90 border border-slate-700/80 rounded-2xl py-3.5 pl-4 pr-12 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:border-indigo-500 transition shadow-inner"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="absolute right-2 p-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 text-white rounded-xl transition disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}