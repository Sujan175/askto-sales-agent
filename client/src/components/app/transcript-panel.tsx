"use client";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Coins, MessageSquareQuote } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { Bot } from "../animate-ui/icons/bot";
import { User } from "../animate-ui/icons/user";

interface TranscriptMessage {
  role: "ai" | "user";
  text: string;
}

interface TranscriptPanelProps {
  transcript: TranscriptMessage[];
  tokensRemaining: number;
  totalTokens: number;
  coinsUsed: number;
  coinsRemaining: number;
  maxCoins: number;
  tokensPerCoin: number;
  isUserSpeaking?: boolean;
  isConfigLoading?: boolean;
}

export function TranscriptPanel({
  transcript,
  tokensRemaining,
  totalTokens,
  coinsUsed,
  coinsRemaining,
  maxCoins,
  tokensPerCoin,
  isUserSpeaking = false,
  isConfigLoading = false,
}: TranscriptPanelProps) {
  const tokensUsed = totalTokens - tokensRemaining;
  const isDevelopment = process.env.NODE_ENV === "development";

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      {/* Header with Quota Counter */}

      <div className="p-4 border-b border-white/10">
        <div className="flex items-center justify-end gap-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Coins className="w-5 h-5 text-green-400" />
            </TooltipTrigger>
            <TooltipContent className="bg-black/90 border border-white/10 text-white text-xs rounded-md px-3 py-2 whitespace-nowrap z-10 shadow-lg">
              <div className="font-semibold mb-1">Coins used</div>
            </TooltipContent>
          </Tooltip>
          <div className="flex items-center gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                {isConfigLoading ? (
                  <Skeleton className="h-4 w-20" />
                ) : (
                  <span className="text-xs text-white/70 font-mono cursor-pointer">
                    {coinsUsed.toFixed(2)} / {maxCoins}
                  </span>
                )}
              </TooltipTrigger>
              <TooltipContent className="bg-black/90 border border-white/10 text-white text-xs rounded-md px-3 py-2 whitespace-nowrap z-10 shadow-lg">
                <div className="font-semibold mb-1">
                  Coins Remaining: {coinsRemaining.toFixed(2)} / {maxCoins}
                </div>
                {isDevelopment && (
                  <div className="text-white/70 border-t border-white/10 pt-1 mt-1">
                    <div>
                      Tokens Used: {tokensUsed.toLocaleString()} /{" "}
                      {totalTokens.toLocaleString()}
                    </div>
                    <div className="text-white/50 text-[10px] mt-0.5">
                      ({tokensPerCoin} tokens = 1 coin)
                    </div>
                  </div>
                )}
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
      </div>

      {/* Transcript List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin relative">
        {transcript.length === 0 && !isUserSpeaking ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-white/70">
            <MessageSquareQuote className="w-6 h-6 mb-2 text-white/50" />
            <p className="text-xs text-center">
              Start the call to initiate transcription
            </p>
          </div>
        ) : (
          <div className="p-4 space-y-4">
            {transcript.map((message, index) => (
              <div key={index} className="flex gap-3">
                <Avatar className="w-8 h-8 shrink-0">
                  <AvatarFallback className="bg-background border-white">
                    {message.role === "ai" ? (
                      <Bot className="w-4 h-4 text-green-500" />
                    ) : (
                      <User className="w-4 h-4 text-white" />
                    )}
                  </AvatarFallback>
                </Avatar>

                <div className="flex-1">
                  <p className="text-xs text-muted-foreground mb-1">
                    {message.role === "ai" ? "Assistant" : "You"}
                  </p>
                  <p
                    className={`text-sm leading-relaxed ${message.role === "ai" ? "text-muted-foreground" : ""
                      }`}
                  >
                    {message.text}
                  </p>
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isUserSpeaking && (
              <div className="flex gap-3">
                <Avatar className="w-8 h-8 shrink-0">
                  <AvatarFallback className="bg-background border-white">
                    <User className="w-4 h-4 text-white" />
                  </AvatarFallback>
                </Avatar>

                <div className="flex-1">
                  <p className="text-xs text-muted-foreground mb-1">You</p>
                  <div className="flex gap-1">
                    <span
                      className="w-2 h-2 bg-current rounded-full animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    />
                    <span
                      className="w-2 h-2 bg-current rounded-full animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    />
                    <span
                      className="w-2 h-2 bg-current rounded-full animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
