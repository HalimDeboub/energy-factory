import { Bot } from "lucide-react";

export function TypingIndicator() {
  return (
    <div className="flex gap-3 justify-start">
      <div className="size-8 rounded-full bg-green-600 flex items-center justify-center flex-shrink-0">
        <Bot className="size-5 text-white" />
      </div>
      <div className="px-4 py-3 rounded-lg bg-white border border-gray-200">
        <div className="flex gap-1">
          <div className="size-2 rounded-full bg-gray-400 animate-bounce [animation-delay:-0.3s]"></div>
          <div className="size-2 rounded-full bg-gray-400 animate-bounce [animation-delay:-0.15s]"></div>
          <div className="size-2 rounded-full bg-gray-400 animate-bounce"></div>
        </div>
      </div>
    </div>
  );
}
