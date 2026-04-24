"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { 
  HiOutlineChatBubbleLeftRight, 
  HiOutlineCpuChip, 
  HiOutlinePaperAirplane,
  HiOutlineCommandLine,
  HiOutlineUsers,
  HiOutlineCube,
  HiOutlineBolt,
  HiOutlineFingerPrint,
  HiOutlineArrowPath,
  HiOutlineCircleStack,
  HiOutlineDocumentMagnifyingGlass,
  HiOutlineKey,
  HiOutlineShieldCheck,
  HiOutlineGlobeAlt,
  HiOutlineTrophy,
  HiOutlineAdjustmentsHorizontal,
  HiOutlineLockClosed,
  HiOutlineChevronDown,
  HiOutlineServer,
  HiOutlineListBullet,
  HiOutlineTrash
} from "react-icons/hi2";
import { AgentShimmer } from "./components/agent-shimmer";

type ChatMode = "AGENT" | "ARENA" | "NORMAL" | "BYOK";

const markdownComponents: Components = {
  code({ className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || "");
    return match ? (
      <div className="relative group/code">
        <pre className="bg-slate-950 p-6 rounded-2xl border border-slate-800 overflow-x-auto my-6 scrollbar-thin scrollbar-thumb-slate-700">
          <code className={className} {...props}>
            {children}
          </code>
        </pre>
        <button
          onClick={() => {
            navigator.clipboard.writeText(String(children));
            alert("Copied to clipboard!");
          }}
          className="absolute top-4 right-4 px-3 py-1.5 bg-slate-800 text-[10px] font-bold text-slate-400 rounded-md opacity-0 group-hover/code:opacity-100 transition-opacity border border-slate-700 uppercase"
        >
          Copy
        </button>
      </div>
    ) : (
      <code className="bg-slate-800 px-2 py-1 rounded text-blue-300 font-mono text-xs" {...props}>
        {children}
      </code>
    );
  },
};

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  thinking?: string;
  tokens?: number;
  agents?: string[];
  consensus?: boolean;
  model_a?: string;
  model_b?: string;
}

const thinkingModes = [
  { id: "fast", label: "Fast", color: "blue" },
  { id: "deliberate", label: "Deliberate", color: "emerald" },
  { id: "deep", label: "Deep", color: "purple" },
  { id: "strategic", label: "Strategic", color: "orange" },
  { id: "critical", label: "Critical", color: "red" },
];

const MODES = [
  { id: "AGENT", label: "Agent Swarm", icon: <HiOutlineUsers />, desc: "Lead by Hang Tuah" },
  { id: "ARENA", label: "LLM vs LLM", icon: <HiOutlineTrophy />, desc: "Competitive Arena" },
  { id: "NORMAL", label: "Normal Chat", icon: <HiOutlineChatBubbleLeftRight />, desc: "Direct Interaction" },
  { id: "BYOK", label: "Keys (BYOK)", icon: <HiOutlineKey />, desc: "Provider Access" },
];

const SOVEREIGN_MODELS = [
  { id: "jebat-cpp-multi", name: "Jebat.cpp Multi-LLM", provider: "Jebat Core", type: "Local/Private" },
  { id: "llama3.1:70b", name: "Llama 3.1 70B", provider: "Ollama", type: "Local" },
  { id: "qwen2.5-coder", name: "Qwen 2.5 Coder", provider: "Ollama", type: "Local" },
];

const BYOK_MODELS = [
  { id: "claude-3-5-sonnet", name: "Claude 3.5 Sonnet", provider: "Anthropic", type: "BYOK/Cloud" },
  { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI", type: "BYOK/Cloud" },
  { id: "gemini-1.5-pro", name: "Gemini 1.5 Pro", provider: "Google", type: "BYOK/Cloud" },
  { id: "z-ai-ultra", name: "Z.AI Ultra", provider: "Z.AI", type: "BYOK/Cloud" },
];

const ALL_MODELS = [...SOVEREIGN_MODELS, ...BYOK_MODELS];

const TECH_QUOTES = [
  { text: "There are only two hard things in Computer Science: cache invalidation and naming things.", author: "Phil Karlton" },
  { text: "Code is like humor. When you have to explain it, it’s bad.", author: "Cory House" },
  { text: "First, solve the problem. Then, write the code.", author: "John Johnson" },
  { text: "Cybersecurity is a shared responsibility, and it's only as strong as the weakest link.", author: "Kevin Mitnick" },
  { text: "The best error message is the one that never shows up.", author: "Thomas Fuchs" },
  { text: "In the world of zero-days, trust no one, verify everything.", author: "SecOps Pro" },
  { text: "Simplicity is the soul of efficiency.", author: "Austin Freeman" },
  { text: "Testing leads to failure, and failure leads to understanding.", author: "Burt Rutan" },
  { text: "One man's constant is another man's variable.", author: "Alan Perlis" },
  { text: "The most dangerous phrase in the language is, 'We've always done it this way.'", author: "Grace Hopper" },
  { text: "Hackers don't break in, they login.", author: "Cyber Intel" },
  { text: "An ounce of prevention is worth a pound of cure.", author: "Benjamin Franklin" },
  { text: "Move fast and break things. Unless you are in production.", author: "DevOps Wisdom" },
];

function TerminalGlitch({ text }: { text: string }) {
  return (
    <div className="relative inline-block group">
      <motion.span
        initial={{ opacity: 1 }}
        animate={{ 
          opacity: [1, 0.8, 1, 0.9, 1],
          x: [0, -0.5, 0.5, -0.5, 0],
        }}
        transition={{ repeat: Infinity, duration: 0.3 }}
        className="relative z-10"
      >
        {text}
      </motion.span>
      <div className="absolute inset-0 z-0 bg-emerald-500/10 blur-sm group-hover:bg-emerald-500/20 transition-all rounded" />
    </div>
  );
}

function ThinkingMarquee() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % TECH_QUOTES.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <AnimatePresence mode="wait">
      <motion.div 
        key={index}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        className="flex items-center gap-3"
      >
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.8)]" />
        <div className="text-[11px] font-bold text-emerald-400 uppercase tracking-[0.12em] font-heading line-clamp-1">
           <TerminalGlitch text={`"${TECH_QUOTES[index].text}"`} />
           <span className="ml-2 text-slate-600 opacity-60">— {TECH_QUOTES[index].author}</span>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

function StreamingMessage({ content, isThinking, isProcessing }: { content: string, isThinking: boolean, isProcessing: boolean }) {
  if (!isThinking && !isProcessing) return null;
  
  return (
    <div className="flex gap-8 justify-start">
      <div className="w-14 h-14 rounded-2xl bg-emerald-600/50 animate-pulse flex-shrink-0 flex items-center justify-center text-white border border-white/5 shadow-2xl">
        <HiOutlineCpuChip className="text-2xl" />
      </div>
      
      <div className="max-w-3xl w-full space-y-6">
        {isThinking && !isProcessing && (
          <div className="flex items-center gap-3 text-[11px] font-bold text-slate-500 uppercase tracking-[0.2em] font-heading animate-pulse">
             <HiOutlineArrowPath className="animate-spin text-emerald-500" /> JEBAT IS SYNTHESIZING RESPONSE...
          </div>
        )}
        
        <div className={`p-10 rounded-[48px] rounded-tl-none text-base leading-relaxed border backdrop-blur-2xl transition-all relative overflow-hidden ${
          isProcessing ? "bg-slate-900/90 border-emerald-500/40 shadow-[0_0_50px_rgba(16,185,129,0.2)]" : "bg-slate-900/40 border-slate-800 shadow-black/20"
        }`}>
          {isProcessing && (
            <div className="absolute inset-0 pointer-events-none opacity-30 bg-[linear-gradient(rgba(18,16,16,0.5)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_3px,4px_100%]" />
          )}

          <div className="prose prose-invert prose-lg max-w-none prose-headings:font-bold prose-headings:text-white prose-strong:text-white prose-ul:list-disc selection:bg-emerald-500/30">
            {isProcessing ? (
                 <>
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                    {content}
                  </ReactMarkdown>
                  <motion.span 
                    animate={{ opacity: [1, 0, 1] }}
                    transition={{ repeat: Infinity, duration: 0.8 }}
                    className="inline-block w-2.5 h-5 bg-emerald-500 ml-1.5 align-middle" 
                  />
                </>
            ) : (
              <div className="space-y-4">
                 <div className="h-5 bg-slate-800 rounded-lg w-3/4 animate-pulse" />
                 <div className="h-5 bg-slate-800 rounded-lg w-full animate-pulse opacity-60" />
                 <div className="h-5 bg-slate-800 rounded-lg w-1/2 animate-pulse opacity-30" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function V3Chat() {
  const [activeMode, setActiveMode] = useState<ChatMode>("AGENT");
  const [selectedModelA, setSelectedModelA] = useState(ALL_MODELS[0]);
  const [selectedModelB, setSelectedModelB] = useState(ALL_MODELS[1]);
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);
  
  const [input, setInput] = useState("");
  const [selectedThinkingMode, setSelectedThinkingMode] = useState("deliberate");
  const [isThinking, setIsThinking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [loadingAgents, setLoadingAgents] = useState<string[]>([]);
  const [thinkingLogs, setThinkingLogs] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Persistence Logic
  useEffect(() => {
    const saved = localStorage.getItem("jebat_v3_sovereign_chat");
    if (saved) {
      try {
        setMessages(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to restore history", e);
      }
    } else {
      setMessages([{ 
        id: "init",
        role: "assistant", 
        content: "Sword of sovereignty active. **[Hang Tuah]** lead orchestrator initialized. Swarm matrix standing by for instructions.",
        consensus: true 
      }]);
    }
    setIsLoaded(true);
  }, []);

  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem("jebat_v3_sovereign_chat", JSON.stringify(messages));
    }
  }, [messages, isLoaded]);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking, streamingContent]);

  const addThinkingLog = (log: string) => {
    setThinkingLogs(prev => [...prev, log]);
  };

  const purgeChat = () => {
    if (confirm("Purge sovereign chat history permanently?")) {
      const reset: Message[] = [{ 
        id: "reset",
        role: "assistant", 
        content: "Memory purged. Neural paths reset. Standing by.",
        consensus: true 
      }];
      setMessages(reset);
      localStorage.removeItem("jebat_v3_sovereign_chat");
    }
  };

  const sendMessage = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || isThinking) return;

    if (activeMode === "BYOK") {
      alert("BYOK mode implementation pending key validation logic.");
      return;
    }

    const userMsg: Message = { 
      id: `user-${Date.now()}`,
      role: "user", 
      content: trimmedInput 
    };
    
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsThinking(true);
    setIsProcessing(false);
    setStreamingContent("");
    setThinkingLogs([]);

    if (activeMode === "AGENT") {
      setLoadingAgents(["Hang Nadim", "Hang Jebat", "Hang Tuah"]);
    }

    try {
      const baseUrl = window.location.origin;
      let response;
      
      try {
        // ATTEMPT 1: High-Performance Streaming via NEW v3 alias (bypasses old SW rules)
        response = await fetch(`${baseUrl}/webui/api/v3/chat?sw-bypass=${Date.now()}`, {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            "bypass-service-worker": "true",
            "x-bypass-sw": "1",
            "Cache-Control": "no-cache, no-store, must-revalidate"
          },
          body: JSON.stringify({
            user_id: "v3_operator",
            message: trimmedInput,
            thinking_mode: selectedThinkingMode
          }),
          cache: "no-store"
        });

        if (!response.ok) throw new Error(`Stream Error: ${response.status}`);
        
        const reader = response.body?.getReader();
        if (!reader) throw new Error("No reader available.");

        const decoder = new TextDecoder();
        let fullContent = "";
        let metadata: any = {};

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (!line.trim()) continue;
            try {
              const data = JSON.parse(line);
              if (data.type === "status") {
                addThinkingLog(`[SYSTEM] ${data.message}`);
              } else if (data.type === "reasoning") {
                addThinkingLog(`[THOUGHT] ${data.content}`);
              } else if (data.type === "content") {
                setIsProcessing(true);
                fullContent += data.delta;
                setStreamingContent(fullContent);
              } else if (data.type === "final") {
                metadata = data;
              } else if (data.type === "error") {
                throw new Error(data.message);
              }
            } catch (e) {
              console.warn("Partial NDJSON.");
            }
          }
        }

        const assistantMsg: Message = {
          id: `assist-${Date.now()}`,
          role: "assistant",
          content: fullContent,
          thinking: `${selectedThinkingMode} mode — ${metadata.execution_time?.toFixed(2) || '0.00'}s execution cycle.`,
          tokens: metadata.tokens || 0,
          agents: activeMode === "AGENT" ? ["Tukang", "Bendahara", "Orchestrator"] : undefined,
          consensus: (metadata.confidence || 0) > 0.8
        };

        setMessages((prev) => [...prev, assistantMsg]);

      } catch (streamError) {
        // ATTEMPT 2: Legacy Fallback (Non-Streaming) via Backend
        console.warn("Streaming failed, initiating Legacy Recovery...", streamError);
        addThinkingLog("⚠️ Stream Interrupted. Initiating Legacy Recovery...");
        
        try {
          const fallbackResponse = await fetch(`${baseUrl}/webui/api/chat?fallback=true&t=${Date.now()}`, {
            method: "POST",
            headers: { 
              "Content-Type": "application/json",
              "bypass-service-worker": "true" 
            },
            body: JSON.stringify({
              user_id: "v3_operator",
              message: trimmedInput,
              thinking_mode: "fast"
            }),
          });

          if (!fallbackResponse.ok) throw new Error("Backend Unreachable");
          
          const data = await fallbackResponse.json();
          const assistantMsg: Message = {
            id: `assist-fallback-${Date.now()}`,
            role: "assistant",
            content: data.response || "Recovery failed. Please check .206 mainframe logs.",
            thinking: "Legacy Recovery Mode Active.",
            consensus: false
          };
          setMessages((prev) => [...prev, assistantMsg]);
        } catch (fallbackError) {
          // ATTEMPT 3: Direct Ollama Recovery (Total Backend Failure)
          console.warn("Backend totally unreachable, hitting Ollama direct...", fallbackError);
          addThinkingLog("🚨 Mainframe Offline. Initiating Direct Ollama Recovery...");
          
          const OLLAMA_DIRECT = "http://72.62.255.206:11434/api/chat";
          const ollamaResponse = await fetch(OLLAMA_DIRECT, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              model: "qwen2.5:14b",
              messages: [{ role: "user", content: trimmedInput }],
              stream: false
            }),
          });

          if (!ollamaResponse.ok) throw new Error("Mainframe and Ollama both offline.");
          
          const data = await ollamaResponse.json();
          const assistantMsg: Message = {
            id: `assist-ollama-${Date.now()}`,
            role: "assistant",
            content: data.message?.content || "Emergency recovery failed.",
            thinking: "Emergency Ollama Direct Mode.",
            consensus: false
          };
          setMessages((prev) => [...prev, assistantMsg]);
        }
      }

      setIsThinking(false);
      setIsProcessing(false);
      setStreamingContent("");
      setLoadingAgents([]);

    } catch (error: any) {
      console.error("Chat Error:", error);
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `**System Error**: ${error.message}\n\nPlease verify VPS connectivity.`,
      };
      setMessages((prev) => [...prev, errorMsg]);
      setIsThinking(false);
      setIsProcessing(false);
      setLoadingAgents([]);
    }
  };

  return (
    <main className="flex-1 flex h-[calc(100vh-5rem)] overflow-hidden font-sans">
      
      <aside className="hidden lg:flex w-80 flex-col border-r border-slate-800/50 bg-slate-950/20 backdrop-blur-md shadow-2xl">
        <div className="p-8 border-b border-slate-800/50 space-y-8">
           <div className="flex items-center gap-3">
              <HiOutlineAdjustmentsHorizontal className="text-emerald-500 text-2xl" />
              <h3 className="text-xs font-bold text-white uppercase tracking-[0.2em] font-heading">Orchestration</h3>
           </div>
           
           <div className="grid grid-cols-1 gap-3">
              {MODES.map(mode => (
                <button
                  key={mode.id}
                  onClick={() => setActiveMode(mode.id as ChatMode)}
                  className={`p-4 rounded-2xl border-2 text-left transition-all flex items-center gap-4 ${
                    activeMode === mode.id 
                    ? "bg-emerald-600 border-emerald-400 text-white shadow-xl shadow-emerald-600/30" 
                    : "bg-slate-900/50 border-slate-800 text-slate-500 hover:border-slate-700 hover:text-white"
                  }`}
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xl ${activeMode === mode.id ? "bg-white/20" : "bg-slate-800 shadow-inner"}`}>
                    {mode.icon}
                  </div>
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-widest">{mode.label}</p>
                    <p className={`text-[9px] font-medium ${activeMode === mode.id ? "text-emerald-100" : "text-slate-600"}`}>{mode.desc}</p>
                  </div>
                </button>
              ))}
           </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-8 space-y-10">
           <div className="space-y-6">
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.2em] font-heading">Model Matrix</p>
              
              <div className="space-y-5">
                 {[
                   { id: 'A', current: selectedModelA, setter: setSelectedModelA, label: activeMode === 'ARENA' ? 'Model A (Primary)' : 'Active LLM Core' },
                   ...(activeMode === 'ARENA' ? [{ id: 'B', current: selectedModelB, setter: setSelectedModelB, label: 'Model B (Competitor)' }] : [])
                 ].map(slot => (
                    <div key={slot.id} className="space-y-3">
                       <label className="text-[10px] font-bold text-slate-600 uppercase ml-1 tracking-widest">{slot.label}</label>
                       <div className="relative group">
                           <select 
                             value={slot.current.id}
                             onChange={(e) => slot.setter(ALL_MODELS.find(m => m.id === e.target.value) || ALL_MODELS[0])}
                             className="w-full bg-slate-900 border-2 border-slate-800 rounded-2xl py-4 px-5 text-xs font-bold text-white appearance-none cursor-pointer focus:border-emerald-500/60 outline-none transition-all shadow-inner"
                           >
                             <optgroup label="Sovereign (Local/Private)" className="bg-slate-900 text-slate-500 italic">
                                {SOVEREIGN_MODELS.map(m => <option key={m.id} value={m.id} className="text-white not-italic font-bold">{m.name}</option>)}
                             </optgroup>
                             <optgroup label="BYOK (Cloud Providers)" className="bg-slate-900 text-slate-500 italic">
                                {BYOK_MODELS.map(m => <option key={m.id} value={m.id} className="text-white not-italic font-bold">{m.name} [BYOK]</option>)}
                             </optgroup>
                          </select>
                          <HiOutlineChevronDown className="absolute right-5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
                       </div>
                    </div>
                 ))}
              </div>
           </div>

           <div className="pt-8 border-t border-slate-800/50 space-y-6">
              <button 
                onClick={purgeChat}
                className="w-full py-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-500 text-[10px] font-bold uppercase tracking-[0.2em] flex items-center justify-center gap-3 hover:bg-red-500 hover:text-white transition-all shadow-lg shadow-red-900/10"
              >
                 <HiOutlineTrash className="text-lg" /> Purge Sovereign History
              </button>
           </div>
        </div>
      </aside>

      {/* ─── Main Workspace ─────────────────────────────── */}
      <section className="flex-1 flex flex-col bg-slate-950/60 relative shadow-inner">
        
        <div className="p-5 border-b border-slate-800/50 flex items-center gap-6 bg-slate-900/10 backdrop-blur-xl z-20">
           <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900/50 border border-slate-800 shadow-sm">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.1em] mr-2">Mode:</span>
              <div className="flex gap-2">
               {activeMode === "BYOK" ? (
                    <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest">Security Vault</span>
                  ) : (
                   thinkingModes.map(m => (
                    <button 
                      key={m.id}
                      onClick={() => setSelectedThinkingMode(m.id)}
                      className={`px-3 py-1 rounded-lg text-[9px] font-bold uppercase transition-all ${
                        selectedThinkingMode === m.id ? `bg-${m.color}-500/20 text-${m.color}-400 border border-${m.color}-500/40 shadow-sm scale-105` : "text-slate-500 hover:text-white"
                      }`}
                    >
                       {m.label}
                    </button>
                  ))
                 )}
              </div>
           </div>
           
           <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900/50 border border-slate-800 ml-auto shadow-sm">
              <HiOutlineShieldCheck className="text-emerald-500 text-lg" />
              <span className="text-[10px] font-bold text-white uppercase tracking-[0.15em]">Sovereignty Active</span>
           </div>
        </div>

        <div className="flex-1 overflow-y-auto p-8 lg:p-12 space-y-12 scroll-smooth custom-scrollbar">
          <AnimatePresence mode="popLayout">
            {activeMode === "BYOK" ? (
               <motion.div 
                 key="byok-view"
                 initial={{ opacity: 0, y: 20 }}
                 animate={{ opacity: 1, y: 0 }}
                 exit={{ opacity: 0, y: -20 }}
                 className="max-w-4xl mx-auto space-y-10"
               >
                <div className="p-12 rounded-[56px] bg-slate-900 border border-slate-800 shadow-3xl space-y-12">
                   <div className="flex items-center gap-5">
                      <div className="w-16 h-16 rounded-3xl bg-emerald-600/10 border-2 border-emerald-500/20 flex items-center justify-center text-emerald-400 text-3xl shadow-inner">
                         <HiOutlineKey />
                      </div>
                      <div>
                         <h3 className="text-3xl font-bold text-white tracking-tight">Access Credentials</h3>
                         <p className="text-slate-500 text-[11px] font-bold uppercase tracking-[0.2em] mt-2">Local persistence — Zero data leakage</p>
                      </div>
                   </div>
                   
                   <div className="space-y-8">
                      {['OpenAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY'].map(key => (
                        <div key={key} className="space-y-4">
                           <label className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.2em] ml-2">{key.replace(/_/g, ' ')}</label>
                           <div className="relative group">
                              <input 
                                type="password"
                                  placeholder="sk-••••••••••••••••"
                                  className="w-full bg-slate-950 border-2 border-slate-800 rounded-[28px] py-5 px-8 text-base focus:outline-none focus:border-blue-500/60 transition-all placeholder:text-slate-800 font-mono shadow-inner text-white"
                                />
                                <HiOutlineLockClosed className="absolute right-8 top-1/2 -translate-y-1/2 text-slate-700 group-hover:text-blue-500 transition-colors text-xl" />
                             </div>
                          </div>
                        ))}
                     </div>

                     <button className="w-full py-5 bg-blue-600 hover:bg-blue-500 text-white rounded-3xl font-bold text-sm uppercase tracking-[0.3em] transition-all shadow-2xl shadow-blue-900/40 transform active:scale-[0.98]">
                        Securely Seal Vault
                     </button>
                  </div>
               </motion.div>
            ) : (
               <div className="max-w-6xl mx-auto w-full space-y-12">
                  {messages.map((msg) => (
                    <motion.div 
                      key={msg.id}
                      initial={{ opacity: 0, scale: 0.98, y: 30 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      className={`flex gap-8 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      {msg.role === 'assistant' && (
                        <div className="w-14 h-14 rounded-2xl bg-blue-600 flex-shrink-0 flex items-center justify-center text-white shadow-2xl shadow-blue-600/40 border-2 border-white/10 mt-2">
                          <HiOutlineCpuChip className="text-2xl" />
                        </div>
                      )}
                      
                      <div className={`max-w-4xl space-y-5 ${msg.role === 'user' ? 'order-1' : 'order-2'}`}>
                        {msg.thinking && (
                          <div className="flex items-center gap-3 text-[11px] font-bold text-blue-500 uppercase tracking-[0.2em] font-heading ml-2">
                             <HiOutlineCommandLine className="text-lg" /> {msg.thinking}
                          </div>
                        )}
                        
                        <div className={`p-10 rounded-[56px] text-base leading-relaxed border-2 shadow-2xl transition-all ${
                          msg.role === 'user' 
                          ? 'bg-blue-600 text-white border-blue-500 rounded-tr-none shadow-blue-900/30' 
                          : 'bg-slate-900/80 text-slate-200 border-slate-800 rounded-tl-none backdrop-blur-2xl shadow-black/60'
                        }`}>
                          <div className="prose prose-invert prose-lg max-w-none prose-headings:font-bold prose-headings:text-white prose-strong:text-blue-400 prose-ul:list-disc selection:bg-blue-500/40">
                            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                              {msg.content}
                            </ReactMarkdown>
                          </div>
                          
                          {msg.consensus && (
                             <div className="mt-8 pt-8 border-t border-slate-800/60 flex items-center gap-4">
                                <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-500 text-lg shadow-inner">
                                   <HiOutlineBolt />
                                </div>
                                <span className="text-[11px] font-bold text-emerald-500 uppercase tracking-[0.25em] font-heading">Sovereign Consensus Verified</span>
                             </div>
                          )}
                        </div>

                        {msg.agents && (
                          <div className="flex flex-wrap gap-3 px-4">
                             {msg.agents.map((agent) => (
                               <div key={agent} className="px-4 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 flex items-center gap-3 shadow-md">
                                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)]"></span>
                                  <span className="text-[10px] font-bold text-white uppercase tracking-[0.15em]">{agent}</span>
                               </div>
                             ))}
                          </div>
                        )}
                      </div>

                      {msg.role === 'user' && (
                        <div className="w-14 h-14 rounded-2xl bg-slate-800 flex-shrink-0 flex items-center justify-center text-slate-400 font-bold border-2 border-slate-700 shadow-2xl shadow-black/50 mt-2 text-lg">
                          HT
                        </div>
                      )}
                    </motion.div>
                  ))}
                  
                  <StreamingMessage 
                    content={streamingContent} 
                    isThinking={isThinking} 
                    isProcessing={isProcessing} 
                  />
               </div>
            )}
          </AnimatePresence>

          {isThinking && (
            <div className="max-w-6xl mx-auto w-full">
               <div className="flex justify-start">
                  <div className="p-10 rounded-[56px] rounded-tl-none border-2 border-slate-800 bg-slate-900/60 backdrop-blur-2xl shadow-3xl space-y-8 min-w-[420px]">
                     <AgentShimmer agents={loadingAgents} visible={isThinking} />
                     <div className="space-y-5 border-t border-slate-800 pt-6">
                        <div className="flex items-center gap-3 text-[11px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-2">
                           <HiOutlineListBullet className="text-blue-500 text-lg" /> Swarm Cognition
                        </div>
                        <div className="space-y-3 max-h-48 overflow-y-auto pr-4 custom-scrollbar">
                           {thinkingLogs.map((log, i) => (
                             <motion.div 
                               key={i}
                               initial={{ opacity: 0, x: -20 }}
                               animate={{ opacity: 1, x: 0 }}
                               className="flex items-start gap-4"
                             >
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
                                <span className="text-[10px] font-mono text-slate-400 leading-relaxed uppercase tracking-widest">{log}</span>
                             </motion.div>
                           ))}
                        </div>
                     </div>
                     <div className="flex items-center gap-4 pt-4 border-t border-slate-800">
                        <ThinkingMarquee />
                     </div>
                  </div>
               </div>
            </div>
          )}
          <div ref={messagesEndRef} className="h-20" />
        </div>

        <footer className={`p-10 border-t-2 border-slate-800 bg-slate-950/90 backdrop-blur-3xl transition-all duration-700 z-30 ${activeMode === 'BYOK' ? 'opacity-0 translate-y-32 pointer-events-none' : 'opacity-100 translate-y-0 shadow-[0_-20px_50px_rgba(0,0,0,0.5)]'}`}>
          <div className="max-w-6xl mx-auto">
            <div className="relative group">
               <input 
                 value={input}
                 onChange={(e) => setInput(e.target.value)}
                 onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                       e.preventDefault();
                       sendMessage();
                    }
                 }}
                 placeholder={
                    activeMode === 'ARENA' ? `Compare ${selectedModelA.name} vs ${selectedModelB.name}...` : 
                    activeMode === 'AGENT' ? `Command the Swarm via ${selectedModelA.name}...` :
                    `Message ${selectedModelA.name} directly...`
                 }
                 className="w-full bg-slate-900/80 border-2 border-slate-800 rounded-[40px] py-8 px-12 text-base focus:outline-none focus:border-blue-500/60 transition-all placeholder:text-slate-700 font-sans shadow-2xl text-white group-hover:border-slate-700"
               />
               <div className="absolute right-8 top-1/2 -translate-y-1/2 flex items-center gap-6">
                  <div className="hidden md:flex items-center gap-6 border-r border-slate-800 pr-8 mr-2">
                     <HiOutlineDocumentMagnifyingGlass className="text-slate-600 text-xl hover:text-blue-500 transition-colors cursor-pointer" title="Deep Recon" />
                     <HiOutlineGlobeAlt className="text-slate-600 text-xl hover:text-blue-500 transition-colors cursor-pointer" title="Global Search" />
                  </div>
                  <button 
                    onClick={sendMessage}
                    disabled={isThinking || !input.trim()}
                    className={`w-16 h-16 rounded-[24px] flex items-center justify-center text-white transition-all shadow-2xl active:scale-90 ${
                      isThinking || !input.trim() 
                      ? "bg-slate-800 text-slate-600 cursor-not-allowed border border-slate-700" 
                      : "bg-blue-600 hover:bg-blue-500 shadow-blue-900/40 border border-blue-400/30"
                    }`}
                  >
                     <HiOutlinePaperAirplane className="rotate-[-45deg] text-2xl" />
                  </button>
               </div>
            </div>
          </div>
        </footer>
      </section>
    </main>
  );
}
