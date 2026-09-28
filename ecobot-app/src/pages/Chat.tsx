import { useState, useRef, useEffect } from "react";
import { Send, Zap, Clock, Database, Sparkles } from "lucide-react";
import { InsightsPanel } from "../components/InsightsPanel";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { useAnalyzeEnergyMutation } from "@/store/api/energyApi";
import { TypingIndicator } from "@/components/TypingIndicator.tsx";
import { MessageBubble } from "../components/MessageBubble";
import { Badge } from "../components/ui/badge";

interface Message {
  id: string;
  role: "user" | "bot";
  content: string;
}

const initialMessages: Message[] = [
  {
    id: "2",
    role: "bot",
    content:
      "I am your Enterprise Energy Assistant. I can help you analyze telemetry from all your connected sources, identify efficiency gaps, and forecast grid demand. How can I assist your mission today?",
  },
];

export function Chat() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [analyzeEnergy, { isLoading }] = useAnalyzeEnergyMutation();
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const scrollToBottom = () => {
      if (messagesContainerRef.current) {
        messagesContainerRef.current.scrollTop =
          messagesContainerRef.current.scrollHeight;
      }
    };
    scrollToBottom();
    const intervalId = setInterval(scrollToBottom, 100);
    return () => clearInterval(intervalId);
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    const userInput = input;
    setInput("");

    try {
      // NOTE: We need to pass the token. Since RTK Query is used, 
      // the baseQuery should be updated to handle this automatically.
      // But for a quick fix if it's not:
      const response = await analyzeEnergy({
        query: userInput,
        session_id: "enterprise_chat"
      }).unwrap();

      if (response.status === "success") {
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "bot",
          content: response.analysis || "Analysis complete.",
        };
        setMessages((prev) => [...prev, botMessage]);
      }
    } catch (error) {
      console.error("Failed to analyze energy:", error);
      setMessages((prev) => [...prev, {
        id: "err", role: "bot", content: "Sorry, I encountered an issue accessing your company's data partition."
      }]);
    }
  };

  return (
    <div className="flex h-full bg-[#fafafa]">
      {/* Chat Area */}
      <div className="flex flex-col flex-1 border-r border-emerald-50">
        {/* Performance Monitor Bar */}
        <div className="flex items-center justify-between px-8 py-3 bg-white border-b border-emerald-50">
          <div className="flex items-center gap-6 text-[10px] font-bold uppercase tracking-widest text-slate-400">
            <span className="flex items-center gap-1.5">
              <Sparkles className="size-3 text-emerald-500" />
              Intelligence: <span className="text-slate-600">Active</span>
            </span>
            <span className="flex items-center gap-1.5">
              <Database className="size-3 text-teal-500" />
              Silo Isolation: <span className="text-slate-600">Secure</span>
            </span>
          </div>
          <div className="flex items-center gap-2">
             <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-none px-3 py-1 rounded-full text-[9px] font-bold tracking-tighter">
               Enterprise RAG v3.0
             </Badge>
          </div>
        </div>

        {/* Messages */}
        <div
          ref={messagesContainerRef}
          className="flex-1 p-8 space-y-6 overflow-y-auto"
        >
          {messages.map((message, index) => (
            <MessageBubble
              key={message.id}
              message={message}
              isLatest={index === messages.length - 1}
            />
          ))}
          {isLoading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 bg-white border-t border-emerald-50 shadow-[0_-10px_40px_rgba(0,0,0,0.02)]">
          <div className="flex max-w-4xl gap-3 mx-auto">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) =>
                e.key === "Enter" && !isLoading && handleSend()
              }
              placeholder="Query your infrastructure data..."
              className="flex-1 bg-slate-50 border-none rounded-2xl h-14 px-6 text-sm focus:ring-2 focus:ring-emerald-100"
              disabled={isLoading}
            />
            <Button
              onClick={handleSend}
              className="bg-emerald-600 hover:bg-emerald-700 h-14 w-14 rounded-2xl shadow-lg shadow-emerald-100 border-none"
              disabled={isLoading}
            >
              <Send className="size-5" />
            </Button>
          </div>
          <p className="text-center text-[10px] text-slate-300 mt-4 uppercase tracking-widest font-medium">
            Authorized session encrypted via AES-256
          </p>
        </div>
      </div>

      {/* Insights Panel */}
      <InsightsPanel />
    </div>
  );
}
