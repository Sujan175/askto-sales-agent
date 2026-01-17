"use client";

import { Phone, Presentation, MessageCircleQuestion } from "lucide-react";
import { Button } from "@/components/ui/button";

export type SessionType = "discovery" | "pitch" | "objection";

interface SessionTypeSelectProps {
  sessionType: SessionType;
  onSessionTypeChange: (type: SessionType) => void;
  disabled?: boolean;
}

const SESSION_TYPE_CONFIG = {
  discovery: {
    label: "Discovery",
    description: "Initial call - Learn about the customer",
    icon: Phone,
  },
  pitch: {
    label: "Pitch",
    description: "Follow-up - Present personalized offer",
    icon: Presentation,
  },
  objection: {
    label: "Objection",
    description: "Final call - Handle concerns",
    icon: MessageCircleQuestion,
  },
} as const;

export function SessionTypeSelect({
  sessionType,
  onSessionTypeChange,
  disabled = false,
}: SessionTypeSelectProps) {
  return (
    <div className="flex flex-col gap-2">
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Session Type
      </span>
      <div className="flex gap-2">
        {(Object.keys(SESSION_TYPE_CONFIG) as SessionType[]).map((type) => {
          const config = SESSION_TYPE_CONFIG[type];
          const Icon = config.icon;
          const isSelected = sessionType === type;

          return (
            <Button
              key={type}
              variant={isSelected ? "default" : "outline"}
              size="sm"
              onClick={() => onSessionTypeChange(type)}
              disabled={disabled}
              className="flex items-center gap-2"
              title={config.description}
            >
              <Icon className="h-4 w-4" />
              <span>{config.label}</span>
            </Button>
          );
        })}
      </div>
    </div>
  );
}
