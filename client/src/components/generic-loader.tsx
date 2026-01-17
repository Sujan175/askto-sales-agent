import { Loader2 } from "lucide-react";

interface GenericLoaderProps {
  title: string;
  loadingMessage: string;
}

export function GenericLoader({ title, loadingMessage }: GenericLoaderProps) {
  return (
    <div>
      <div className="space-y-4 text-center">
        <Loader2 className="mx-auto size-12 animate-spin text-primary" />
        <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
        <p className="text-lg text-muted-foreground">{loadingMessage}</p>
      </div>
    </div>
  );
}
