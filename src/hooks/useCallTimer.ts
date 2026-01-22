import { useState, useEffect, useRef } from "react";

/**
 * Hook to manage call duration timer
 * Replaces the global globalCallStartTime with proper React state
 * @param inCall - Whether the user is currently in a call
 * @returns The call duration in seconds
 */
export function useCallTimer(inCall: boolean): number {
  const [callDuration, setCallDuration] = useState(0);
  const callStartTimeRef = useRef<number | null>(null);

  // Track call start/end
  useEffect(() => {
    if (inCall) {
      if (!callStartTimeRef.current) {
        callStartTimeRef.current = Date.now();
      }
    } else {
      callStartTimeRef.current = null;
      setCallDuration(0);
    }
  }, [inCall]);

  // Update duration every second when in call
  useEffect(() => {
    if (!inCall || !callStartTimeRef.current) return;

    const updateTime = () => {
      if (callStartTimeRef.current) {
        setCallDuration(Math.floor((Date.now() - callStartTimeRef.current) / 1000));
      }
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);

    return () => clearInterval(interval);
  }, [inCall]);

  return callDuration;
}
