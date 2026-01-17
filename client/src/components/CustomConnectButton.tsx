import { Button } from "@/components/ui/button";
import { CircleX, Play } from "lucide-react";

interface CustomConnectButtonProps {
  size?: "sm" | "md" | "lg";
  onConnect?: () => void | Promise<void>;
  onDisconnect?: () => void | Promise<void>;
  connectText?: string;
  disconnectText?: string;
  connectingText?: string;
  isConnected?: boolean;
  isConnecting?: boolean;
}

export function CustomConnectButton({
  size = "md",
  onConnect,
  onDisconnect,
  connectText = "Connect",
  disconnectText = "Disconnect",
  connectingText = "Starting...",
  isConnected = false,
  isConnecting = false,
}: CustomConnectButtonProps) {
  const handleClick = async () => {
    if (isConnected && onDisconnect) {
      await onDisconnect();
    } else if (!isConnected && onConnect) {
      await onConnect();
    }
  };

  const sizeClasses = {
    sm: "h-8 px-3 text-sm",
    md: "h-10 px-4 text-md",
    lg: "h-12 px-6 text-lg",
  };

  const getButtonText = () => {
    if (isConnecting) return connectingText;
    if (isConnected) return disconnectText;
    return connectText;
  };

  return (
    <Button
      onClick={handleClick}
      variant={isConnected ? "destructive" : "default"}
      className={`${sizeClasses[size]} ${!isConnected ? "bg-green-300 hover:bg-green-300 text-black h-[43px]" : "h-[43px]"
        }`}
      disabled={isConnecting}
    >
      {!isConnected ? (
        <Play className="mr-2 h-10 w-10" />
      ) : (
        <CircleX className="mr-2 h-5 w-5" />
      )
      }
      {getButtonText()}
    </Button>
  );
}
