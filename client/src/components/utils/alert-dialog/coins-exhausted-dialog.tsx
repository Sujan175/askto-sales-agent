import {
    AlertDialog,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

interface CoinsExhaustedDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onEndInterview: () => void;
    isEnding: boolean;
}

export function CoinsExhaustedDialog({
    open,
    onOpenChange,
    onEndInterview,
    isEnding,
}: CoinsExhaustedDialogProps) {
    return (
        <AlertDialog open={open} onOpenChange={isEnding ? () => {} : onOpenChange}>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Coins Exhausted</AlertDialogTitle>
                    <AlertDialogDescription>
                        You have exhausted all your coins. Please end the interview to start a new session.
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <Button
                        onClick={onEndInterview}
                        disabled={isEnding}
                        className="min-w-[120px]"
                        variant="destructive"
                    >
                        {isEnding ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Ending...
                            </>
                        ) : (
                            "End Interview"
                        )}
                    </Button>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}
