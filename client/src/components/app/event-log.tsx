"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Bot } from "@/components/animate-ui/icons/bot"
import { User } from "@/components/animate-ui/icons/user"
import { Settings } from "@/components/animate-ui/icons/settings"
import { ChevronUp } from "@/components/animate-ui/icons/chevron-up"
import { ChevronDown } from "@/components/animate-ui/icons/chevron-down"

interface Event {
  time: string
  event: string
  type: "system" | "ai" | "user"
}

interface EventLogProps {
  events: Event[]
}

export function EventLog({ events }: EventLogProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const getEventIcon = (type: Event["type"]) => {
    switch (type) {
      case "system":
        return <Settings className="w-3 h-3" />
      case "ai":
        return <Bot className="w-3 h-3" />
      case "user":
        return <User className="w-3 h-3" />
    }
  }

  const getEventColor = (type: Event["type"]) => {
    switch (type) {
      case "system":
        return "text-yellow-500"
      case "ai":
        return "text-blue-500"
      case "user":
        return "text-green-500"
    }
  }

  return (
    <div className="border-t border-white/10">
      <Button
        variant="ghost"
        className="w-full flex items-center justify-between p-4 hover:bg-white/5"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="text-sm font-medium text-muted-foreground">Event Log ({events.length})</span>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        ) : (
          <ChevronUp className="w-4 h-4 text-muted-foreground" />
        )}
      </Button>

      {isExpanded && (
        <div className="h-48 pb-4 relative">
          {events.length === 0 ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-white/70">
              <Settings className="w-6 h-6 mb-2 text-white/50" />
              <p className="text-xs text-center">No events yet</p>
            </div>
          ) : (
            <div className="h-full overflow-y-auto scrollbar-thin">
              <div className="px-2 space-y-2">
                {events.map((event, index) => (
                  <div key={index} className="flex items-start gap-2 text-xs p-2 rounded bg-white/5">
                    <span className={getEventColor(event.type)}>{getEventIcon(event.type)}</span>
                    <span className="text-muted-foreground font-mono">{event.time}</span>
                    <span className="text-foreground">{event.event}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
