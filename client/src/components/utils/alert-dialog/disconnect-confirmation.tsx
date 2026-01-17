import {
    AlertDialog,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

interface DisconnectConfirmationProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onConfirm: () => void;
    isEnding?: boolean;
}

export function DisconnectConfirmation({
    open,
    onOpenChange,
    onConfirm,
    isEnding = false,
}: DisconnectConfirmationProps) {
    return (
        <AlertDialog open={open} onOpenChange={isEnding ? () => {} : onOpenChange}>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>End Call?</AlertDialogTitle>
                    <AlertDialogDescription>
                        This will end your current call. All transcript and event data will be saved, and your local session data will be cleared. This action cannot be undone.
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel disabled={isEnding}>Cancel</AlertDialogCancel>
                    <Button 
                        onClick={onConfirm} 
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
                            "End Call"
                        )}
                    </Button>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}
