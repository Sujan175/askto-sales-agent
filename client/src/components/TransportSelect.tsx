import { Bot } from "@/components/animate-ui/icons/bot";
import { AnimateIcon } from "@/components/animate-ui/icons/icon";
import { TransportType } from "@/config";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@pipecat-ai/voice-ui-kit";

interface TransportSelectProps {
  transportType: TransportType;
  onTransportChange: (type: TransportType) => void;
  availableTransports: TransportType[];
}

const TRANSPORT_LABELS: Record<TransportType, string> = {
  // daily: 'Daily',
  smallwebrtc: "SmallWebRTC",
};

export const TransportSelect = ({
  transportType,
  onTransportChange,
  availableTransports,
}: TransportSelectProps) => {
  return (
    <div className="flex items-center gap-2 w-full min-w-0 max-w-[200px]">
      <AnimateIcon animateOnHover>
        <Bot className="w-8 h-8 flex-shrink-0 text-green-300" />
      </AnimateIcon>
      <Select value={transportType} onValueChange={onTransportChange}>
        <SelectTrigger className="w-full min-w-0 text-xs h-8">
          <SelectValue placeholder="Select transport" className="truncate">
            <span className="truncate block">
              {TRANSPORT_LABELS[transportType]}
            </span>
          </SelectValue>
        </SelectTrigger>
        <SelectContent position="popper" sideOffset={4}>
          {availableTransports.map((transport) => (
            <SelectItem key={transport} value={transport}>
              {TRANSPORT_LABELS[transport]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};
