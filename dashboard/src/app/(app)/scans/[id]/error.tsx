"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error(error);
    }, [error]);

    return (
        <div className="flex h-[50vh] flex-col items-center justify-center gap-4">
            <div className="flex flex-col items-center gap-2 text-center">
                <AlertCircle className="h-10 w-10 text-destructive" />
                <h2 className="text-xl font-semibold">Something went wrong!</h2>
                <p className="text-sm text-muted-foreground max-w-[500px] break-words">
                    {error.message}
                </p>
                {error.stack && (
                    <pre className="mt-4 max-h-[200px] max-w-[600px] overflow-auto rounded bg-muted p-4 text-left text-xs text-muted-foreground">
                        {error.stack}
                    </pre>
                )}
            </div>
            <Button onClick={() => reset()}>Try again</Button>
        </div>
    );
}
