"use client";

import { useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { GenericLoader } from "@/components/generic-loader";

function DecodeTokenContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");

  useEffect(() => {
    const decodeAndRedirect = async () => {
      if (!token) {
        console.error("No token provided");
        router.push("/");
        return;
      }

      try {
        const response = await fetch("/api/decode-token", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ token }),
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || "Failed to decode token");
        }

        // Store decoded data in sessionStorage for use on home page
        sessionStorage.setItem("interviewData", JSON.stringify(data.decoded));
        localStorage.setItem("authToken", token);

        // Redirect to home page
        router.push("/");
      } catch (err: any) {
        console.error("Token verification failed:", err.message);
        // Redirect to home even on error
        router.push("/");
      }
    };

    decodeAndRedirect();
  }, [token, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <GenericLoader
        title="Verifying token..."
        loadingMessage="Redirecting to interview..."
      />
    </div>
  );
}

export default function DecodeTokenPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
          <GenericLoader title="Loading..." loadingMessage="Please wait..." />
        </div>
      }
    >
      <DecodeTokenContent />
    </Suspense>
  );
}
