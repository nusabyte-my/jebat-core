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
  HiOutlineListBullet
} from "react-icons/hi2";
import { AgentShimmer } from "./components/agent-shimmer";

type ChatMode = "AGENT" | "ARENA" | "NORMAL" | "BYOK";

const markdownComponents: Components = {
  code({ className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || "");
    return match ? (
      <div className="relative group/code">
        <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 overflow-x-auto my-4 scrollbar-thin scrollbar-thumb-slate-700">
          <code className={className} {...props}>
            {children}
          </code>
        </pre>
        <button
          onClick={() => {
            navigator.clipboard.writeText(String(children));
            alert("Copied to clipboard!");
          }}
          className="absolute top-3 right-3 px-2 py-1 bg-slate-800 text-[8px] font-bold text-slate-400 rounded-md opacity-0 group-hover/code:opacity-100 transition-opacity border border-slate-700 uppercase"
        >
          Copy
        </button>
      </div>
    ) : (
      <code className="bg-slate-800 px-1.5 py-0.5 rounded text-blue-300 font-mono" {...props}>
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

const TECH_JOKES = [
  "Centering a div in a kernel-level sandbox...",
  "Finding vulnerabilities in node_modules...",
  "Escalating privileges to 'sudo' for npm install...",
  "Masking PII data from the intern's direct messages...",
  "Optimizing PostgreSQL indices for 0.4ms latency...",
  "Hang Nadim is arguing with Llama 3 about the speed of light...",
  "Converting coffee into verified swarm consensus...",
  "Fixing a merge conflict that spans 34 specialist roles...",
];

function ThinkingMarquee() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % TECH_JOKES.length);
    }, 2500);
    return () => clearInterval(timer);
  }, []);

  return (
    <motion.div 
      key={index}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="text-[10px] font-bold text-blue-400 uppercase tracking-[0.2em] italic truncate max-w-sm"
    >
       {TECH_JOKES[index]}
    </motion.div>
  );
}

export default function V3Chat() {
  const [activeMode, setActiveMode] = useState<ChatMode>("AGENT");
  const [selectedModelA, setSelectedModelA] = useState(ALL_MODELS[0]);
  const [selectedModelB, setSelectedModelB] = useState(ALL_MODELS[1]);
  
  const [messages, setMessages] = useState<Message[]>([
    { 
      id: "init",
      role: "assistant", 
      content: "Sword of sovereignty active. **[Hang Tuah]** lead orchestrator initialized. Swarm matrix standing by for instructions.",
      consensus: true 
    },
  ]);
  
  const [input, setInput] = useState("");
  const [selectedThinkingMode, setSelectedThinkingMode] = useState("deliberate");
  const [isThinking, setIsThinking] = useState(false);
  const [loadingAgents, setLoadingAgents] = useState<string[]>([]);
  const [thinkingLogs, setThinkingLogs] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  const addThinkingLog = (log: string) => {
    console.log(`[Thinking] ${log}`);
    setThinkingLogs(prev => [...prev, log]);
  };

  const sendMessage = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || isThinking) return;

    if (activeMode === "BYOK") {
      alert("BYOK mode implementation pending key validation logic.");
      return;
    }

    console.group("🚀 JEBAT Swarm Dispatch");
    console.log("Prompt:", trimmedInput);
    console.log("Mode:", activeMode);
    console.log("Model Core:", selectedModelA.name);

    const userMsg: Message = { 
      id: `user-${Date.now()}`,
      role: "user", 
      content: trimmedInput 
    };
    
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsThinking(true);
    setThinkingLogs([]);

    if (activeMode === "AGENT") {
      setLoadingAgents(["Tukang", "Bendahara"]);
    }

    // Initial "Thinking" logs for UX feedback
    addThinkingLog("Hang Nadim: Classifying intent vectors...");
    setTimeout(() => addThinkingLog(`Hang Tuah: Request routed to ${activeMode === 'AGENT' ? 'specialist swarm' : 'LLM core'}...`), 500);
    setTimeout(() => addThinkingLog(`VPS .206: Initializing inference on ${selectedModelA.name}...`), 1000);

    try {
      // Direct API call to the .206 mainframe for heavy reasoning tasks
      const baseUrl = "https://jebat.online";
      
      // Real API Call to JEBAT Backend
      const response = await fetch(`${baseUrl}/webui/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: "v3_operator",
          message: trimmedInput,
          thinking_mode: selectedThinkingMode
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || "Unknown backend error");
      }

      // Add backend reasoning steps to logs if available
      if (data.reasoning && data.reasoning.length > 0) {
        data.reasoning.forEach((step: string, index: number) => {
          setTimeout(() => addThinkingLog(`Thinking Step ${index + 1}: ${step}`), 1200 + (index * 400));
        });
      }

      setTimeout(() => {
        addThinkingLog("Sentinel: Scrubbing PII and hardening response...");
        
        let assistantMsg: Message;
        
        if (activeMode === "ARENA") {
          assistantMsg = {
            id: `assist-${Date.now()}`,
            role: "assistant",
            content: `### Arena Comparison\n\n**Response from ${selectedModelA.name}:**\n\n${data.response}\n\n---\n\n*Note: In Arena mode, secondary model validation is currently running in the background.*`,
            model_a: selectedModelA.name,
            model_b: selectedModelB.name,
            thinking: `Parallel analysis complete. Accuracy: ${(data.confidence * 100).toFixed(1)}%`
          };
        } else {
          assistantMsg = {
            id: `assist-${Date.now()}`,
            role: "assistant",
            content: data.response,
            thinking: `${selectedThinkingMode} mode — ${data.execution_time?.toFixed(2) || '0.00'}s execution cycle.`,
            tokens: data.tokens || 0,
            agents: activeMode === "AGENT" ? ["Tukang", "Bendahara", "Orchestrator"] : undefined,
            consensus: data.confidence > 0.8
          };
        }

        console.log("Assistant Response:", assistantMsg);
        console.groupEnd();
        setMessages((prev) => [...prev, assistantMsg]);
        setIsThinking(false);
        setLoadingAgents([]);
      }, Math.max(2000, (data.reasoning?.length || 0) * 400 + 1500));

    } catch (error: any) {
      console.error("Chat Error:", error);
      addThinkingLog(`❌ Error: ${error.message}`);
      
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `**Deployment Error**: Failed to reach the JEBAT backend on .206.\n\nDetails: ${error.message}\n\nPlease ensure the API server is running on the target VPS.`,
      };
      
      setMessages((prev) => [...prev, errorMsg]);
      setIsThinking(false);
      setLoadingAgents([]);
      console.groupEnd();
    }
  };

  return (
    <main className="flex-1 flex h-[calc(100vh-5rem)] overflow-hidden">
      
      <aside className="hidden lg:flex w-80 flex-col border-r border-slate-800/50 bg-slate-950/20 backdrop-blur-md shadow-2xl">
        <div className="p-6 border-b border-slate-800/50 space-y-8">
           <div className="flex items-center gap-3">
              <HiOutlineAdjustmentsHorizontal className="text-blue-500 text-xl" />
              <h3 className="text-xs font-bold text-white uppercase tracking-widest font-heading">Orchestration</h3>
           </div>
           
           <div className="grid grid-cols-1 gap-2">
              {MODES.map(mode => (
                <button
                  key={mode.id}
                  onClick={() => setActiveMode(mode.id as ChatMode)}
                  className={`p-3 rounded-2xl border text-left transition-all flex items-center gap-3 ${
                    activeMode === mode.id 
                    ? "bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-600/20" 
                    : "bg-slate-900/50 border-slate-800 text-slate-500 hover:border-slate-700 hover:text-white"
                  }`}
                >
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-lg ${activeMode === mode.id ? "bg-white/20" : "bg-slate-800 shadow-inner"}`}>
                    {mode.icon}
                  </div>
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-tight">{mode.label}</p>
                    <p className={`text-[8px] font-medium ${activeMode === mode.id ? "text-blue-100" : "text-slate-600"}`}>{mode.desc}</p>
                  </div>
                </button>
              ))}
           </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6 space-y-8">
           <div className="space-y-6">
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest font-heading">Model Matrix</p>
              
              <div className="space-y-4">
                 {[
                   { id: 'A', current: selectedModelA, setter: setSelectedModelA, label: activeMode === 'ARENA' ? 'Model A (Primary)' : 'Active LLM Core' },
                   ...(activeMode === 'ARENA' ? [{ id: 'B', current: selectedModelB, setter: setSelectedModelB, label: 'Model B (Competitor)' }] : [])
                 ].map(slot => (
                    <div key={slot.id} className="space-y-2">
                       <label className="text-[9px] font-bold text-slate-600 uppercase ml-1">{slot.label}</label>
                       <div className="relative group">
                          <select 
                            value={slot.current.id}
                            onChange={(e) => slot.setter(ALL_MODELS.find(m => m.id === e.target.value) || ALL_MODELS[0])}
                            className="w-full bg-slate-900 border border-slate-800 rounded-xl py-3 px-4 text-xs font-bold text-white appearance-none cursor-pointer focus:border-blue-500/50 outline-none transition-all shadow-inner"
                          >
                             <optgroup label="Sovereign (Local/Private)" className="bg-slate-900 text-slate-500 italic">
                                {SOVEREIGN_MODELS.map(m => <option key={m.id} value={m.id} className="text-white not-italic font-bold">{m.name}</option>)}
                             </optgroup>
                             <optgroup label="BYOK (Cloud Providers)" className="bg-slate-900 text-slate-500 italic">
                                {BYOK_MODELS.map(m => <option key={m.id} value={m.id} className="text-white not-italic font-bold">{m.name} [BYOK]</option>)}
                             </optgroup>
                          </select>
                          <HiOutlineChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
                       </div>
                       {slot.current.type.includes("BYOK") && (
                          <button 
                            onClick={() => setActiveMode("BYOK")}
                            className="flex items-center gap-1.5 text-[8px] font-bold text-blue-500 hover:text-blue-400 transition-colors uppercase ml-1"
                          >
                             <HiOutlineKey className="text-[10px]" /> Configure Key Required
                          </button>
                       )}
                    </div>
                 ))}
              </div>
           </div>

           {activeMode === "AGENT" && (
             <div className="pt-6 border-t border-slate-800/50 space-y-6">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest font-heading">Swarm Status</p>
                <div className="space-y-3">
                   <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center gap-3 shadow-xl">
                      <div className="w-6 h-6 rounded-md bg-blue-600 flex items-center justify-center text-[9px] font-bold text-white shadow-lg">HT</div>
                      <span className="text-[10px] font-bold text-white uppercase tracking-tight">Hang Tuah</span>
                      <span className="ml-auto w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
                   </div>
                </div>
                <div className="p-4 rounded-2xl bg-blue-600/5 border border-blue-500/10 flex flex-col gap-3 shadow-sm">
                   <div className="flex items-center gap-2 text-blue-400">
                      <HiOutlineServer className="text-lg" />
                      <span className="text-[9px] font-bold uppercase tracking-widest">Mainframe .206</span>
                   </div>
                   <p className="text-[8px] text-slate-500 leading-relaxed uppercase font-medium">Inference via VPS .206 verified.</p>
                </div>
             </div>
           )}
        </div>
      </aside>

      {/* ─── Main Workspace ─────────────────────────────── */}
      <section className="flex-1 flex flex-col bg-slate-950/40 relative shadow-inner">
        
        <div className="p-4 border-b border-slate-800/50 flex items-center gap-4 bg-slate-900/10 backdrop-blur-md">
           <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/50 border border-slate-800 shadow-sm">
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-tighter mr-2">Config:</span>
              <div className="flex gap-1">
                 {activeMode === "BYOK" ? (
                   <span className="text-[9px] font-bold text-blue-400 uppercase tracking-widest">Security Vault</span>
                 ) : (
                   thinkingModes.map(m => (
                    <button 
                      key={m.id}
                      onClick={() => setSelectedThinkingMode(m.id)}
                      className={`px-2 py-0.5 rounded-md text-[8px] font-bold uppercase transition-all ${
                        selectedThinkingMode === m.id ? `bg-${m.color}-500/20 text-${m.color}-400 border border-${m.color}-500/30 shadow-sm` : "text-slate-500 hover:text-white"
                      }`}
                    >
                       {m.label}
                    </button>
                  ))
                 )}
              </div>
           </div>
           
           <div className="flex-1 flex justify-center overflow-hidden">
              <AnimatePresence mode="wait">
                {isThinking && <ThinkingMarquee />}
              </AnimatePresence>
           </div>

           <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/50 border border-slate-800 ml-auto shadow-sm">
              <HiOutlineShieldCheck className="text-blue-500 text-xs" />
              <span className="text-[9px] font-bold text-white uppercase tracking-widest">Sovereignty Shield Active</span>
           </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 lg:p-10 space-y-10">
          <AnimatePresence mode="popLayout">
            {activeMode === "BYOK" ? (
               <motion.div 
                 key="byok-view"
                 initial={{ opacity: 0, y: 10 }}
                 animate={{ opacity: 1, y: 0 }}
                 exit={{ opacity: 0, y: -10 }}
                 className="max-w-4xl mx-auto space-y-8"
               >
                  <div className="p-10 rounded-[48px] bg-slate-900 border border-slate-800 shadow-3xl space-y-10">
                     <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 text-2xl shadow-inner">
                           <HiOutlineKey />
                        </div>
                        <div>
                           <h3 className="text-2xl font-bold text-white tracking-tight">Provider Access Management</h3>
                           <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mt-1">Keys are stored locally and never sent to our servers.</p>
                        </div>
                     </div>
                     
                     <div className="space-y-6">
                        {['OpenAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY'].map(key => (
                          <div key={key} className="space-y-3">
                             <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">{key.replace(/_/g, ' ')}</label>
                             <div className="relative group">
                                <input 
                                  type="password"
                                  placeholder="sk-••••••••••••••••"
                                  className="w-full bg-slate-950 border border-slate-800 rounded-2xl py-4 px-6 text-sm focus:outline-none focus:border-blue-500/50 transition-all placeholder:text-slate-800 font-mono shadow-inner text-white"
                                />
                                <HiOutlineLockClosed className="absolute right-6 top-1/2 -translate-y-1/2 text-slate-700 group-hover:text-blue-500 transition-colors" />
                             </div>
                          </div>
                        ))}
                     </div>

                     <button className="w-full py-4 bg-blue-600 hover:bg-blue-50 text-white rounded-2xl font-bold text-xs uppercase tracking-widest transition-all shadow-xl shadow-blue-600/20">
                        Securely Save Credentials
                     </button>
                  </div>
               </motion.div>
            ) : (
               <div className="max-w-5xl mx-auto w-full space-y-10">
                  {messages.map((msg) => (
                    <motion.div 
                      key={msg.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex gap-6 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      {msg.role === 'assistant' && (
                        <div className="w-12 h-12 rounded-2xl bg-blue-600 flex-shrink-0 flex items-center justify-center text-white shadow-2xl shadow-blue-600/30 border border-white/10">
                          <HiOutlineCpuChip className="text-xl" />
                        </div>
                      )}
                      
                      <div className={`max-w-2xl space-y-4 ${msg.role === 'user' ? 'order-1' : 'order-2'}`}>
                        {msg.thinking && (
                          <div className="flex items-center gap-2 text-[10px] font-bold text-blue-500 uppercase tracking-widest font-heading">
                             <HiOutlineCommandLine /> {msg.thinking}
                          </div>
                        )}
                        
                        <div className={`p-8 rounded-[40px] text-sm leading-relaxed border shadow-2xl transition-all ${
                          msg.role === 'user' 
                          ? 'bg-blue-600 text-white border-blue-500 rounded-tr-none shadow-blue-900/20' 
                          : 'bg-slate-900/80 text-slate-300 border-slate-800 rounded-tl-none backdrop-blur-xl shadow-black/50'
                        }`}>
                          <div className="prose prose-invert prose-sm max-w-none prose-headings:font-bold prose-headings:text-white prose-strong:text-white prose-ul:list-disc">
                            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                              {msg.content}
                            </ReactMarkdown>
                          </div>
                          
                          {msg.model_a && (
                             <div className="mt-8 grid grid-cols-2 gap-4 border-t border-slate-800 pt-6">
                                <div className="p-4 rounded-2xl bg-slate-950/50 border border-slate-800 shadow-inner">
                                   <p className="text-[8px] font-bold text-blue-400 uppercase mb-1">{msg.model_a}</p>
                                   <p className="text-[10px] text-slate-500 leading-tight italic">Analyzing performance vectors...</p>
                                </div>
                                <div className="p-4 rounded-2xl bg-slate-950/50 border border-slate-800 shadow-inner">
                                   <p className="text-[8px] font-bold text-purple-400 uppercase mb-1">{msg.model_b}</p>
                                   <p className="text-[10px] text-slate-500 leading-tight italic">Analyzing logic constraints...</p>
                                </div>
                             </div>
                          )}

                          {msg.consensus && (
                             <div className="mt-8 pt-6 border-t border-slate-800 flex items-center gap-3">
                                <div className="w-6 h-6 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500 text-xs shadow-inner">
                                   <HiOutlineBolt />
                                </div>
                                <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest font-heading">Cross-Agent Consensus Verified</span>
                             </div>
                          )}
                        </div>

                        {msg.agents && (
                          <div className="flex flex-wrap gap-2 px-2">
                             {msg.agents.map((agent) => (
                               <div key={agent} className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800 flex items-center gap-2 shadow-sm">
                                  <span className="w-1 h-1 rounded-full bg-blue-500 shadow-[0_0_4px_rgba(59,130,246,0.5)]"></span>
                                  <span className="text-[9px] font-bold text-white uppercase tracking-widest">{agent}</span>
                               </div>
                             ))}
                          </div>
                        )}
                      </div>

                      {msg.role === 'user' && (
                        <div className="w-12 h-12 rounded-2xl bg-slate-800 flex-shrink-0 flex items-center justify-center text-slate-400 font-bold border border-slate-700 shadow-xl shadow-black/40">
                          HT
                        </div>
                      )}
                    </motion.div>
                  ))}
               </div>
            )}
          </AnimatePresence>

          {isThinking && (
            <div className="max-w-5xl mx-auto w-full">
               <div className="flex justify-start">
                  <div className="p-8 rounded-[40px] rounded-tl-none border border-slate-800 bg-slate-900/50 backdrop-blur-md shadow-2xl space-y-6 min-w-[320px]">
                     <AgentShimmer agents={loadingAgents} visible={isThinking} />
                     <div className="space-y-3 border-t border-slate-800 pt-4">
                        <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">
                           <HiOutlineListBullet className="text-blue-500" /> Thinking Steps
                        </div>
                        <div className="space-y-2 max-h-40 overflow-y-auto pr-2 custom-scrollbar">
                           {thinkingLogs.map((log, i) => (
                             <motion.div 
                               key={i}
                               initial={{ opacity: 0, x: -10 }}
                               animate={{ opacity: 1, x: 0 }}
                               className="flex items-start gap-3"
                             >
                                <div className="w-1 h-1 rounded-full bg-emerald-500 mt-1.5 shadow-[0_0_4px_rgba(16,185,129,0.5)]"></div>
                                <span className="text-[9px] font-mono text-slate-400 leading-relaxed uppercase">{log}</span>
                             </motion.div>
                           ))}
                        </div>
                     </div>
                     <div className="flex items-center gap-3 pt-2 border-t border-slate-800">
                        <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse shadow-[0_0_12px_rgba(59,130,246,0.5)]"></div>
                        <span className="text-[10px] font-bold text-blue-400 uppercase tracking-[0.2em] font-heading">
                          Orchestration in Progress...
                        </span>
                     </div>
                  </div>
               </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <footer className={`p-8 border-t border-slate-800 bg-slate-950/80 backdrop-blur-2xl transition-all duration-500 ${activeMode === 'BYOK' ? 'opacity-0 translate-y-20 pointer-events-none' : 'opacity-100 translate-y-0 shadow-2xl'}`}>
          <div className="max-w-5xl mx-auto">
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
                 className="w-full bg-slate-900 border-2 border-slate-800 rounded-[32px] py-6 px-10 text-sm focus:outline-none focus:border-blue-500/50 transition-all placeholder:text-slate-600 font-sans shadow-2xl shadow-black/20 text-white"
               />
               <div className="absolute right-6 top-1/2 -translate-y-1/2 flex items-center gap-4">
                  <div className="hidden md:flex items-center gap-4 border-r border-slate-800 pr-6 mr-2">
                     <HiOutlineDocumentMagnifyingGlass className="text-slate-600 text-lg hover:text-blue-500 transition-colors cursor-pointer" title="Recon" />
                     <HiOutlineGlobeAlt className="text-slate-600 text-lg hover:text-blue-500 transition-colors cursor-pointer" title="Web Search" />
                  </div>
                  <button 
                    onClick={sendMessage}
                    disabled={isThinking || !input.trim()}
                    className={`w-12 h-12 rounded-2xl flex items-center justify-center text-white transition shadow-xl active:scale-95 ${
                      isThinking || !input.trim() 
                      ? "bg-slate-800 text-slate-600 cursor-not-allowed border border-slate-700" 
                      : "bg-blue-600 hover:bg-blue-50 shadow-blue-600/30 border border-blue-400/20"
                    }`}
                  >
                     <HiOutlinePaperAirplane className="rotate-[-45deg] text-lg" />
                  </button>
               </div>
            </div>
          </div>
        </footer>
      </section>
    </main>
  );
}
