import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { InsightsPanel } from "../components/InsightsPanel";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { useAnalyzeEnergyMutation } from "@/store/api/energyApi";
import { TypingIndicator } from "@/components/TypingIndicator.tsx";
import { MessageBubble } from "../components/MessageBubble";

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
      "i am your energy assistant, here to help you save energy and reduce your carbon footprint. ask me anything about energy efficiency, solar power, or sustainability tips!",
  },
];

export function Chat() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [analyzeEnergy, { isLoading }] = useAnalyzeEnergyMutation();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
      // Call the backend API with correct payload format
      const response = await analyzeEnergy({
        query: userInput,
        keep_alive: -1,
      }).unwrap();

      if (response.status === "success") {
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "bot",
          content:
            response.analysis ||
            "Analysis complete. How can I help you further?",
        };

        setMessages((prev) => [...prev, botMessage]);
      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "bot",
          content:
            response.message ||
            "Sorry, I encountered an error processing your request.",
        };

        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error("Failed to analyze energy:", error);

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "bot",
        content:
          "Sorry, I'm having trouble connecting to the server. Please make sure the API is running on http://localhost:9000",
      };

      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  return (
    <div className="flex h-full">
      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message, index) => (
            <MessageBubble
              key={message.id}
              message={message}
              isLatest={index === messages.length - 1}
            />
          ))}

          {/* Typing indicator */}
          {isLoading && <TypingIndicator />}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 bg-white p-4">
          <div className="flex gap-2 max-w-4xl mx-auto">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) =>
                e.key === "Enter" && !isLoading && handleSend()
              }
              placeholder="Ask about energy savings, solar power, or sustainability tips..."
              className="flex-1"
              disabled={isLoading}
            />
            <Button
              onClick={handleSend}
              className="bg-green-600 hover:bg-green-700"
              disabled={isLoading}
            >
              <Send className="size-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Insights Panel */}
      <InsightsPanel />
    </div>
  );
}
