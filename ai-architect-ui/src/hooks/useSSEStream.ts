import { useCallback, useRef } from 'react';
import { streamChat } from '../api/chat';
import { useStore } from '../store/useStore';

/**
 * Hook that manages SSE streaming via fetch + ReadableStream.
 * Returns a `send` function that starts the stream and an `abort` function.
 */
export function useSSEStream() {
  const abortRef = useRef<AbortController | null>(null);
  const token = useStore((s) => s.token);
  const conversationId = useStore((s) => s.conversationId);
  const handleEvent = useStore((s) => s.handleEvent);
  const setStreaming = useStore((s) => s.setStreaming);
  const setError = useStore((s) => s.setError);
  const beginUserTurn = useStore((s) => s.beginUserTurn);
  const abortStreaming = useStore((s) => s.abortStreaming);

  const send = useCallback(
    async (message: string) => {
      if (!token) {
        setError('Not authenticated');
        return;
      }

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setStreaming(true);
      setError(null);
      beginUserTurn(message);

      try {
        await streamChat(
          token,
          message,
          conversationId ?? undefined,
          handleEvent,
          controller.signal,
        );
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          setError((err as Error).message ?? 'Stream failed');
        }
      } finally {
        setStreaming(false);
      }
    },
    [token, conversationId, handleEvent, setStreaming, setError, beginUserTurn],
  );

  const abort = useCallback(() => {
    abortRef.current?.abort();
    abortStreaming();
  }, [abortStreaming]);

  return { send, abort };
}
