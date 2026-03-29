import { Bot, User } from "lucide-react";
import { useTypewriter } from "@/hooks/useTypewriter";

interface MessageBubbleProps {
  message: {
    id: string;
    role: "user" | "bot";
    content: string;
  };
  isLatest: boolean;
}

export function MessageBubble({ message, isLatest }: MessageBubbleProps) {
  // Only use typewriter effect for the latest bot message
  const shouldType = message.role === "bot" && isLatest;
  const { displayedText, isTyping } = useTypewriter({
    text: shouldType ? message.content : "",
    speed: 30,
  });

  const displayContent = shouldType ? displayedText : message.content;

  return (
    <div
      className={`flex gap-3 ${
        message.role === "user" ? "justify-end" : "justify-start"
      }`}
    >
      {message.role === "bot" && (
        <div className="size-8 rounded-full bg-green-600 flex items-center justify-center flex-shrink-0">
          <Bot className="size-5 text-white" />
        </div>
      )}
      <div
        className={`max-w-2xl px-4 py-3 rounded-lg ${
          message.role === "user"
            ? "bg-green-600 text-white"
            : "bg-white border border-gray-200 text-gray-800"
        }`}
      >
        <p className="whitespace-pre-wrap">
          {displayContent}
          {isTyping && (
            <span className="inline-block w-1 h-4 ml-1 bg-gray-400 animate-pulse"></span>
          )}
        </p>
      </div>
      {message.role === "user" && (
        <div className="size-8 rounded-full bg-gray-600 flex items-center justify-center flex-shrink-0">
          <User className="size-5 text-white" />
        </div>
      )}
    </div>
  );
}
