import type { AgentEvent } from '../types/api';

const STREAM_URL = '/api/v1/chat/stream';

/**
 * POST to the SSE streaming endpoint using fetch + ReadableStream.
 * NOT EventSource — the endpoint requires POST with a JSON body.
 */
export async function streamChat(
  token: string,
  message: string,
  conversationId: string | undefined,
  onEvent: (event: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(STREAM_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message, conversationId }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Stream request failed: ${res.status} ${text}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        // SSE format: lines prefixed with "data: "
        const data = trimmed.startsWith('data:')
          ? trimmed.slice(5).trim()
          : trimmed;

        if (!data || data === '[DONE]') continue;

        try {
          const event: AgentEvent = JSON.parse(data);
          onEvent(event);
        } catch {
          // skip unparseable lines
        }
      }
    }

    // flush remaining buffer
    if (buffer.trim()) {
      const data = buffer.trim().startsWith('data:')
        ? buffer.trim().slice(5).trim()
        : buffer.trim();
      if (data && data !== '[DONE]') {
        try {
          const event: AgentEvent = JSON.parse(data);
          onEvent(event);
        } catch {
          // skip
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
