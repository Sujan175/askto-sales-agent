"use client"

import { useState } from "react"
import { AnimatedOrb } from "./animated-orb"
import { EventLog } from "./event-log"
import { TranscriptPanel } from "./transcript-panel"
import { Avatar, AvatarFallback, AvatarImage} from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { VolumeOff } from "@/components/animate-ui/icons/volume-off"
import { Volume2 } from "@/components/animate-ui/icons/volume-2"
import { PhoneCall } from "@/components/animate-ui/icons/phone-call"

export default function AIInterview() {
  const [isSpeaking, setIsSpeaking] = useState<"ai" | "user" | null>(null)
  const [isMuted, setIsMuted] = useState(false)
  const [tokensRemaining, setTokensRemaining] = useState(4500)
  const [transcript, setTranscript] = useState([
    {
      role: "ai" as const,
      text: "Hello! Welcome to your AI interview. I'm excited to learn more about you today. Let's start with a simple question - can you tell me about yourself?",
    },
    { role: "user" as const, text: "Hi! Thanks for having me. I'm a software developer with 5 years of experience..." },
    {
      role: "ai" as const,
      text: "That's great! Your experience sounds impressive. What would you say is your biggest strength?",
    },
  ])
  const [events, setEvents] = useState([
    { time: "00:00:01", event: "Session started", type: "system" as const },
    { time: "00:00:02", event: "AI greeting initiated", type: "ai" as const },
    { time: "00:00:15", event: "User response detected", type: "user" as const },
    { time: "00:00:45", event: "AI follow-up question", type: "ai" as const },
  ])

  // Simulate speaking states
  const simulateAISpeaking = () => {
    setIsSpeaking("ai")
    setTimeout(() => setIsSpeaking(null), 3000)
  }

  const simulateUserSpeaking = () => {
    setIsSpeaking("user")
    setTimeout(() => setIsSpeaking(null), 2000)
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex">
      {/* Main Interview Area */}
      <div className="flex-1 flex flex-col items-center justify-center relative">
        {/* Cursor Tracking Robot */}

        {/* Central Orb / Avatar Display */}
        <div className="relative">
          {isSpeaking === "user" ? (
            <div className="relative">
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-green-500/30 via-emerald-500/30 to-teal-500/30 blur-3xl animate-pulse" />
              <Avatar className="w-48 h-48 border-4 border-green-500/50 relative z-10">
                <AvatarImage src="/placeholder-user.png" />
                <AvatarFallback className="text-4xl bg-gradient-to-br from-green-600 to-emerald-700">U</AvatarFallback>
              </Avatar>
              <div className="absolute -inset-4 rounded-full border-2 border-green-500/30 animate-ping" />
            </div>
          ) : (
            <AnimatedOrb isAnimating={isSpeaking === "ai"} />
          )}
        </div>

        {/* Status Text */}
        <p className="mt-8 text-lg text-muted-foreground">
          {isSpeaking === "ai" && "AI is speaking..."}
          {isSpeaking === "user" && "Listening to you..."}
          {!isSpeaking && "Ready for your response"}
        </p>

        {/* Control Buttons */}
        <div className="flex gap-4 mt-8">
          <Button
            variant="outline"
            size="lg"
            className="rounded-full w-14 h-14 bg-white/5 border-white/10 hover:bg-white/10"
            onClick={() => setIsMuted(!isMuted)}
          >
            {isMuted ? <VolumeOff className="w-6 h-6" /> : <Volume2 className="w-6 h-6" />}
          </Button>
          <Button variant="destructive" size="lg" className="rounded-full w-14 h-14">
            <PhoneCall className="w-6 h-6" />
          </Button>
        </div>

        {/* Demo Buttons */}
        <div className="flex gap-2 mt-6">
          <Button variant="ghost" size="sm" onClick={simulateAISpeaking}>
            Simulate AI Speaking
          </Button>
          <Button variant="ghost" size="sm" onClick={simulateUserSpeaking}>
            Simulate User Speaking
          </Button>
        </div>
      </div>

      {/* Right Sidebar */}
      <div className="w-96 bg-[#111118] border-l border-white/10 flex flex-col">
        <TranscriptPanel
          transcript={transcript}
          tokensRemaining={tokensRemaining}
          totalTokens={5000}
          coinsUsed={0}
          coinsRemaining={0}
          maxCoins={0}
          tokensPerCoin={0}
        />
        <EventLog events={events} />
      </div>
    </div>
  )
}
