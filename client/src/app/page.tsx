"use client";

import { useState, useMemo } from "react";

import { ThemeProvider } from "@pipecat-ai/voice-ui-kit";

import type { PipecatBaseChildProps } from "@pipecat-ai/voice-ui-kit";
import {
  FullScreenContainer,
  PipecatAppBase,
  SpinLoader,
} from "@pipecat-ai/voice-ui-kit";

import {
  AVAILABLE_TRANSPORTS,
  DEFAULT_TRANSPORT,
  TRANSPORT_CONFIG,
} from "../config";
import type { TransportType } from "../config";
import { App } from "@/components/App";
import type { SessionType } from "@/components/SessionTypeSelect";

import {
  generateInterviewPrompt,
  getInterviewData,
} from "../utils/prompt-builder";

export default function Home() {
  const [transportType, setTransportType] =
    useState<TransportType>(DEFAULT_TRANSPORT);
  const [sessionType, setSessionType] = useState<SessionType>("discovery");

  const connectParams = useMemo(() => {
    const baseConfig = TRANSPORT_CONFIG[transportType];

    // For LangGraph mode (sales agent), we pass sessionType instead of systemPrompt
    // The server will use the appropriate prompt based on session type
    let systemPrompt =
      "You are a helpful and friendly interviewer. You help candidates stay cool and composed during interviews, but you give answers in short form.";

    // Check if we're in interview mode (legacy) or sales mode (LangGraph)
    const isInterviewMode = typeof window !== "undefined" && getInterviewData();

    if (isInterviewMode) {
      try {
        const interviewData = getInterviewData();
        if (interviewData) {
          systemPrompt = generateInterviewPrompt(interviewData);
        }
      } catch (error) {
        console.error("Failed to build dynamic prompt:", error);
      }
    }

    return {
      endpoint: baseConfig.endpoint,
      requestData: {
        ...(baseConfig.requestData as Record<string, any>),
        systemPrompt: isInterviewMode ? systemPrompt : undefined,
        sessionType: isInterviewMode ? undefined : sessionType,
      },
    };
  }, [transportType, sessionType]);

  return (
    <ThemeProvider defaultTheme="terminal" disableStorage>
      <FullScreenContainer>
        <PipecatAppBase
          connectParams={connectParams}
          transportType={transportType}
        >
          {({
            client,
            handleConnect,
            handleDisconnect,
            error,
          }: PipecatBaseChildProps) =>
            !client ? (
              <SpinLoader />
            ) : error ? (
              <div className="flex items-center justify-center h-screen w-full">
                <div className="text-center space-y-2">
                  <h2 className="text-2xl font-semibold">Error</h2>
                  <p className="text-muted-foreground">{error}</p>
                </div>
              </div>
            ) : (
              <App
                client={client}
                handleConnect={handleConnect}
                handleDisconnect={handleDisconnect}
                transportType={transportType}
                onTransportChange={setTransportType}
                availableTransports={AVAILABLE_TRANSPORTS}
                sessionType={sessionType}
                onSessionTypeChange={setSessionType}
              />
            )
          }
        </PipecatAppBase>
      </FullScreenContainer>
    </ThemeProvider>
  );
}
