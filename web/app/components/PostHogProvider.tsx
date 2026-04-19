"use client";
import { useEffect } from "react";
import { initPostHog, posthog } from "@/app/lib/posthog";

export function PostHogProvider() {
  useEffect(() => {
    initPostHog();
    const advanced = !!posthog.getFeatureFlag?.("aifp-monte-carlo-advanced");
    posthog.capture?.("monte_carlo_mode_seen", {
      mode: advanced ? "advanced" : "basic",
    });
  }, []);
  return null;
}
