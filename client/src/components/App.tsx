import { useEffect, useState } from "react";
import type { PipecatBaseChildProps } from "@pipecat-ai/voice-ui-kit";
import { UserAudioControl } from "@pipecat-ai/voice-ui-kit";
import { RTVIEvent } from "@pipecat-ai/client-js";
import { BookOpenText, FileText } from "lucide-react";
import { toast } from "sonner";

import { TransportType } from "@/config";
import { TransportSelect } from "./TransportSelect";
import { CustomConnectButton } from "./CustomConnectButton";
import { AnimatedOrb } from "./app/animated-orb";
import { TranscriptPanel } from "./app/transcript-panel";
import { EventLog } from "./app/event-log";
import { saveInterview } from "@/lib/interview";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarProvider,
  SidebarInset,
  useSidebar,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { DisconnectConfirmation } from "./utils/alert-dialog/disconnect-confirmation";
import { CoinsExhaustedDialog } from "./utils/alert-dialog/coins-exhausted-dialog";
import { SessionTypeSelect, type SessionType } from "./SessionTypeSelect";

interface AppProps extends PipecatBaseChildProps {
  transportType: TransportType;
  onTransportChange: (type: TransportType) => void;
  availableTransports: TransportType[];
  sessionType?: SessionType;
  onSessionTypeChange?: (type: SessionType) => void;
}

interface TokenUsageData {
  tokens_used: number;
  max_tokens: number;
  tokens_remaining: number;
  coins_used: number;
  coins_remaining: number;
  max_coins: number;
  tokens_per_coin: number;
}

const AppContent = ({
  client,
  handleConnect,
  handleDisconnect,
  transportType,
  onTransportChange,
  availableTransports,
  sessionType = "discovery",
  onSessionTypeChange,
}: AppProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [transcript, setTranscript] = useState<
    Array<{ role: "ai" | "user"; text: string }>
  >([]);
  const [events, setEvents] = useState<
    Array<{ time: string; event: string; type: "system" | "ai" | "user" }>
  >([]);
  const [maxTokens, setMaxTokens] = useState(10000);
  const [tokensUsed, setTokensUsed] = useState(0);
  const [tokensRemaining, setTokensRemaining] = useState(10000);
  const [coinsUsed, setCoinsUsed] = useState(0);
  const [coinsRemaining, setCoinsRemaining] = useState(10);
  const [maxCoins, setMaxCoins] = useState(10);
  const [tokensPerCoin, setTokensPerCoin] = useState(1000);
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);
  const [isBotSpeaking, setIsBotSpeaking] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showDisconnectAlert, setShowDisconnectAlert] = useState(false);
  const [showCoinExhausted, setShowCoinExhausted] = useState(false);
  const [isEndingCall, setIsEndingCall] = useState(false);
  const [isConfigLoading, setIsConfigLoading] = useState(true);
  const [voiceId, setVoiceId] = useState<string | null>(null);
  const { toggleSidebar, open } = useSidebar();

  useEffect(() => {
    const storedSessionId = sessionStorage.getItem("sessionId");
    if (storedSessionId) {
      setSessionId(storedSessionId);
      const storedTranscript = sessionStorage.getItem("transcript");
      if (storedTranscript) {
        setTranscript(JSON.parse(storedTranscript));
      }
      const storedEvents = sessionStorage.getItem("events");
      if (storedEvents) {
        setEvents(JSON.parse(storedEvents));
      }
      const storedTokensUsed = sessionStorage.getItem("tokensUsed");
      if (storedTokensUsed) {
        const used = parseInt(storedTokensUsed);
        setTokensUsed(used);
      }
    }
  }, []);

  useEffect(() => {
    const fetchConfig = async () => {
      setIsConfigLoading(true);
      try {
        const response = await fetch("/api/config");
        if (response.ok) {
          const config = await response.json();
          setMaxTokens(config.max_tokens);
          setMaxCoins(config.max_coins);
          setTokensPerCoin(config.tokens_per_coin);
          if (config.voice_id) {
            setVoiceId(config.voice_id);
          }

          const storedTokensUsed = sessionStorage.getItem("tokensUsed");
          if (storedTokensUsed) {
            const used = parseInt(storedTokensUsed);
            const coins = used / config.tokens_per_coin;
            setCoinsUsed(coins);
            setCoinsRemaining(Math.max(config.max_coins - coins, 0));
            setTokensRemaining(Math.max(config.max_tokens - used, 0));
          } else {
            setTokensRemaining(config.max_tokens);
            setCoinsRemaining(config.max_coins);
          }
        }
      } catch (error) {
        console.error("Failed to fetch config:", error);
      } finally {
        setIsConfigLoading(false);
      }
    };
    fetchConfig();
  }, []);

  useEffect(() => {
    if (sessionId) {
      sessionStorage.setItem("transcript", JSON.stringify(transcript));
      sessionStorage.setItem("events", JSON.stringify(events));
      sessionStorage.setItem("tokensUsed", tokensUsed.toString());
    }
  }, [transcript, events, sessionId, tokensUsed]);

  useEffect(() => {
    client?.initDevices();
  }, [client]);

  useEffect(() => {
    if (!client) return;

    // Listen for bot ready
    const handleBotReady = () => {
      setIsConnected(true);
      const time = new Date().toLocaleTimeString();
      setEvents((prev) => [
        ...prev,
        { time, event: "Bot connected", type: "system" },
      ]);

      setTimeout(() => {
        if (sessionId) {
          const storedTokensUsed = sessionStorage.getItem("tokensUsed");
          client.transport.sendMessage({
            id: Math.random().toString(36).slice(2),
            label: "rtvi-ai",
            type: "client-message",
            data: {
              t: "session_resume",
              d: {
                session_id: sessionId,
                tokens_used: storedTokensUsed ? parseInt(storedTokensUsed) : 0,
              },
            },
          });
          setEvents((prev) => [
            ...prev,
            { time, event: `Resuming session: ${sessionId}`, type: "system" },
          ]);
        }
      }, 100);
    };

    // Listen for transcripts
    const handleUserTranscript = (data: any) => {
      setTranscript((prev) => [...prev, { role: "user", text: data.text }]);
      const time = new Date().toLocaleTimeString();
      setEvents((prev) => [
        ...prev,
        { time, event: "User spoke", type: "user" },
      ]);
      setIsUserSpeaking(false);
    };

    const handleBotTranscript = (data: any) => {
      setTranscript((prev) => [...prev, { role: "ai", text: data.text }]);
      const time = new Date().toLocaleTimeString();
      setEvents((prev) => [...prev, { time, event: "Bot spoke", type: "ai" }]);
      setIsBotSpeaking(false);
    };

    // Listen for user started speaking
    const handleUserStartedSpeaking = () => {
      setIsUserSpeaking(true);
      const time = new Date().toLocaleTimeString();
      setEvents((prev) => [
        ...prev,
        { time, event: "User started speaking", type: "user" },
      ]);
    };

    // Listen for bot started speaking
    const handleBotStartedSpeaking = () => {
      setIsBotSpeaking(true);
      const time = new Date().toLocaleTimeString();
      setEvents((prev) => [
        ...prev,
        { time, event: "Bot started speaking", type: "ai" },
      ]);
    };

    const handleBotStoppedSpeaking = () => {
      setIsBotSpeaking(false);
    };

    const processTokenUsage = (tokenData: TokenUsageData) => {
      setMaxTokens(tokenData.max_tokens);
      setTokensUsed(tokenData.tokens_used);
      setTokensRemaining(tokenData.tokens_remaining);
      setCoinsUsed(tokenData.coins_used);
      setCoinsRemaining(tokenData.coins_remaining);
      setMaxCoins(tokenData.max_coins);
      setTokensPerCoin(tokenData.tokens_per_coin);
      // const time = new Date().toLocaleTimeString();
      // setEvents((prev) => [
      //   ...prev,
      //   {
      //     time,
      //     event: `Coins: ${tokenData.coins_used.toFixed(2)}/${tokenData.max_coins
      //       } (${tokenData.tokens_per_coin} tokens/coin)`,
      //     type: "system",
      //   },
      // ]);
    };

    const handleServerMessage = (message: any) => {
      // if (message?.type === "ping") {
      //   const time = new Date().toLocaleTimeString();
      //   setEvents((prev) => [
      //     ...prev,
      //     {
      //       time,
      //       event: `TEST PING: ${JSON.stringify(message.data)}`,
      //       type: "system",
      //     },
      //   ]);
      // }
      if (message?.type === "token_limit_exceeded") {
        const time = new Date().toLocaleTimeString();
        setEvents((prev) => [
          ...prev,
          {
            time,
            event: `ERROR: ${message.data.message}`,
            type: "system",
          },
        ]);
        setShowCoinExhausted(true);
        return;
      }
      if (message?.type === "session_init") {
        if (!sessionId) {
          const newSessionId = message.data.session_id;
          setSessionId(newSessionId);
          sessionStorage.setItem("sessionId", newSessionId);
        } else {
          // console.log(
          //   `Ignoring session_init ${message.data.session_id} because we are resuming ${sessionId}`
          // );
        }
      } else if (message?.type === "token_usage") {
        const tokenData = message.data;

        if (
          tokenData &&
          tokenData.tokens_used !== undefined &&
          tokenData.tokens_remaining !== undefined
        ) {
          processTokenUsage(tokenData as TokenUsageData);
        } else {
          console.error(
            "Token usage message missing required fields:",
            message
          );
        }
      } else {
        // console.log(
        //   "Other server message type:",
        //   message?.type || "unknown"
        // );
      }
    };

    client.on("botReady", handleBotReady);
    client.on("userTranscript", handleUserTranscript);
    client.on("botTranscript", handleBotTranscript);
    client.on("serverMessage", handleServerMessage);
    client.on("userStartedSpeaking", handleUserStartedSpeaking);
    client.on("botStartedSpeaking", handleBotStartedSpeaking);
    client.on("botStoppedSpeaking", handleBotStoppedSpeaking);

    return () => {
      client.off("botReady", handleBotReady);
      client.off("userTranscript", handleUserTranscript);
      client.off("botTranscript", handleBotTranscript);
      client.off("serverMessage", handleServerMessage);
      client.off("userStartedSpeaking", handleUserStartedSpeaking);
      client.off("botStartedSpeaking", handleBotStartedSpeaking);
      client.off("botStoppedSpeaking", handleBotStoppedSpeaking);
    };
  }, [client, sessionId]);

  const handleConnectWrapper = async () => {
    if (handleConnect) {
      setIsConnecting(true);
      try {
        await handleConnect();
      } catch (error: any) {
        const status = error?.status || error?.response?.status;

        if (status === 401) {
          toast.error("User not authorized", {
            description: "Authentication failed. Please log in again.",
          });
        } else if (status === 500) {
          toast.error("Server Error", {
            description: "Internal server error. Please try again later.",
          });
        } else {
          toast.error("Connection Failed", {
            description: "Failed to start the call. Please try again.",
          });
        }
        console.error("Connection error:", error);
      } finally {
        setIsConnecting(false);
      }
    }
  };

  const handleDisconnectClick = () => {
    setShowDisconnectAlert(true);
  };

  const handleDisconnectWrapper = async () => {
    let saveSuccessful = false;
    try {
      if (sessionId) {
        const interviewDataStr = sessionStorage.getItem("interviewData");
        let userId: string | undefined;
        let jobId: string | undefined;

        if (interviewDataStr) {
          try {
            const interviewData = JSON.parse(interviewDataStr);
            userId = interviewData.user?.user_id;
            jobId = interviewData.job?.job_id?.toString();
          } catch (err) {
            console.error("Failed to parse interviewData:", err);
          }
        }

        // Only save interview data if we have userId and jobId (interview mode)
        if (!userId || !jobId) {
          console.log("No interview data to save (sales agent mode)");
          // Clear session data without saving
          sessionStorage.removeItem("sessionId");
          sessionStorage.removeItem("transcript");
          sessionStorage.removeItem("events");
          sessionStorage.removeItem("tokensUsed");
          
          setSessionId(null);
          setTranscript([]);
          setEvents([]);
          setTokensUsed(0);
          setCoinsUsed(0);
          saveSuccessful = true;
        } else {
          const details = {
            user_id: userId,
            job_id: jobId,
            transcript: transcript,
            created_at: new Date(),
            updated_at: new Date(),
            id: Math.random().toString(36).slice(2),
            transport_used: transportType,
            voice_id: voiceId || "unknown",
            token_used: tokensUsed,
            max_token: maxTokens,
            event_logs: events,
            coins_used: coinsUsed,
            max_coins: maxCoins,
            tokens_per_coin: tokensPerCoin,
            session_id: sessionId,
          };

          try {
            await saveInterview(details);
            saveSuccessful = true;
          } catch (saveError: any) {
            // Handle authentication errors specifically
            if (saveError.status === 401 || saveError.status === 403) {
              toast.error("Authentication failed", {
                description:
                  saveError.message ||
                  "Your session has expired. Please log in again.",
              });
              // Clear stored data on auth failure
              localStorage.removeItem("authToken");
              sessionStorage.removeItem("interviewData");
            } else {
              // For other errors, show the actual error message
              toast.error("Failed to save interview", {
                description:
                  saveError.message ||
                  "There was an error saving your interview data.",
              });
            }
            // Don't throw - we'll handle cleanup below
          }

          // Only clear session data if save was successful
          if (saveSuccessful) {
            sessionStorage.removeItem("sessionId");
            sessionStorage.removeItem("transcript");
            sessionStorage.removeItem("events");
            sessionStorage.removeItem("tokensUsed");

            setSessionId(null);
            setTranscript([]);
            setEvents([]);
            setTokensUsed(0);
            setCoinsUsed(0);
          }
        }
      }

      if (handleDisconnect) {
        handleDisconnect();
      }
      setIsConnected(false);
      const time = new Date().toLocaleTimeString();
      setEvents((prev) => [
        ...prev,
        { time, event: "Bot disconnected", type: "system" },
      ]);
      setEvents((prev) => [
        ...prev,
        { time, event: "Session ended", type: "system" },
      ]);

      // Only show success toast if we have a session and save was successful
      if (sessionId && saveSuccessful) {
        toast.success("Call ended successfully", {
          description: "Your call has ended. Have a great day!",
        });
      }
    } catch (error) {
      console.error("Error ending session:", error);
      toast.error("Failed to end session", {
        description:
          "There was an error ending your session. Please try again.",
      });
    } finally {
      setIsEndingCall(false);
      setShowCoinExhausted(false);
      setShowDisconnectAlert(false);
    }
  };

  const handleDisconnectConfirmation = async () => {
    setIsEndingCall(true);
    await handleDisconnectWrapper();
  };

  const handleCoinExhaustedEnd = async () => {
    setIsEndingCall(true);
    await handleDisconnectWrapper();
  };

  // const showTransportSelector = availableTransports.length > 1;

  return (
    <div className="flex w-full h-screen bg-background overflow-hidden">
      <SidebarInset className="flex flex-col flex-1 bg-background relative">
        <div className="absolute top-4 left-4 z-50 flex flex-col gap-4">
          {/* {showTransportSelector && ( */}
          <TransportSelect
            transportType={transportType}
            onTransportChange={onTransportChange}
            availableTransports={availableTransports}
          />
          {/* )} */}
          {onSessionTypeChange && (
            <SessionTypeSelect
              sessionType={sessionType}
              onSessionTypeChange={onSessionTypeChange}
              disabled={isConnected}
            />
          )}
        </div>

        <div className="absolute top-4 right-4 z-50">
          <Button
            variant="outline"
            className="border lg:hidden flex items-center gap-2 px-4 h-8 w-auto bg-background/50 backdrop-blur-sm hover:bg-background/80"
            onClick={toggleSidebar}
          >
            <BookOpenText className="h-4 w-4" />
            <span className="font-semibold">Transcript</span>
          </Button>
        </div>

        <div className="flex w-full h-full items-center justify-center flex-1">
          {/* Center - Animated Orb and Controls */}
          <div className="flex flex-col items-center justify-center gap-8 p-8 w-full max-w-3xl">
            <AnimatedOrb isAnimating={isBotSpeaking} />

            <div className="flex flex-col items-center gap-4">
              <div className="flex items-center gap-4">
                <UserAudioControl size="lg" />
                <CustomConnectButton
                  size="md"
                  onConnect={handleConnectWrapper}
                  onDisconnect={handleDisconnectClick}
                  connectText="Start Call"
                  disconnectText="End Call"
                  isConnected={isConnected}
                  isConnecting={isConnecting}
                />
              </div>
            </div>
          </div>
        </div>
      </SidebarInset>

      <Sidebar side="right" collapsible="offcanvas">
        <SidebarContent className="h-full overflow-hidden">
          <div className="h-full flex flex-col overflow-hidden scrollbar-thin">
            <TranscriptPanel
              transcript={transcript}
              tokensRemaining={tokensRemaining}
              totalTokens={maxTokens}
              coinsUsed={coinsUsed}
              coinsRemaining={coinsRemaining}
              maxCoins={maxCoins}
              tokensPerCoin={tokensPerCoin}
              isUserSpeaking={isUserSpeaking}
              isConfigLoading={isConfigLoading}
            />
            <EventLog events={events} />
          </div>
        </SidebarContent>
      </Sidebar>

      <DisconnectConfirmation
        open={showDisconnectAlert}
        onOpenChange={setShowDisconnectAlert}
        onConfirm={handleDisconnectConfirmation}
        isEnding={isEndingCall}
      />

      <CoinsExhaustedDialog
        open={showCoinExhausted}
        onOpenChange={setShowCoinExhausted}
        onEndCall={handleCoinExhaustedEnd}
        isEnding={isEndingCall}
      />
    </div>
  );
};

export const App = (props: AppProps) => {
  return (
    <SidebarProvider defaultOpen={true}>
      <AppContent {...props} />
    </SidebarProvider>
  );
};
