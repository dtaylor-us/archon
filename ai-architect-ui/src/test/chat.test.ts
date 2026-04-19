import { describe, it, expect, vi, beforeEach } from 'vitest';
import { streamChat } from '../api/chat';
import type { AgentEvent } from '../types/api';

// Helper to create a ReadableStream from string chunks
function makeStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  let index = 0;
  return new ReadableStream({
    pull(controller) {
      if (index < chunks.length) {
        controller.enqueue(encoder.encode(chunks[index]));
        index++;
      } else {
        controller.close();
      }
    },
  });
}

describe('streamChat', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('parsesSSEDataLinesAndCallsOnEvent', async () => {
    const events: AgentEvent[] = [];
    const chunks = [
      'data: {"type":"STAGE_START","stage":"requirement_parsing"}\n',
      'data: {"type":"CHUNK","content":"hello"}\n',
      'data: {"type":"COMPLETE","payload":{"conversationId":"c1"}}\n',
    ];

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: makeStream(chunks),
    } as unknown as Response);

    await streamChat('token', 'message', undefined, (e) => events.push(e));

    expect(events).toHaveLength(3);
    expect(events[0].type).toBe('STAGE_START');
    expect(events[1].type).toBe('CHUNK');
    expect(events[1].content).toBe('hello');
    expect(events[2].type).toBe('COMPLETE');
  });

  it('parsesRawNDJSONLinesWithoutDataPrefix', async () => {
    const events: AgentEvent[] = [];
    const chunks = [
      '{"type":"STAGE_START","stage":"req"}\n{"type":"COMPLETE","payload":{}}\n',
    ];

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: makeStream(chunks),
    } as unknown as Response);

    await streamChat('token', 'msg', 'conv-1', (e) => events.push(e));

    expect(events).toHaveLength(2);
  });

  it('skipsUnparseableLines', async () => {
    const events: AgentEvent[] = [];
    const chunks = [
      'data: not-json\n',
      'data: {"type":"CHUNK","content":"ok"}\n',
    ];

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: makeStream(chunks),
    } as unknown as Response);

    await streamChat('token', 'msg', undefined, (e) => events.push(e));

    expect(events).toHaveLength(1);
    expect(events[0].content).toBe('ok');
  });

  it('throwsOnNon200Response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 401,
      text: async () => 'Unauthorized',
    } as unknown as Response);

    await expect(
      streamChat('bad-token', 'msg', undefined, () => {}),
    ).rejects.toThrow('401');
  });

  it('throwsWhenNoResponseBody', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: null,
    } as unknown as Response);

    await expect(
      streamChat('token', 'msg', undefined, () => {}),
    ).rejects.toThrow('No response body');
  });

  it('handlesChunkedDataSplitAcrossReads', async () => {
    const events: AgentEvent[] = [];
    // Simulate data split across two reads
    const chunks = [
      'data: {"type":"CHUNK",',
      '"content":"split"}\n',
    ];

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: makeStream(chunks),
    } as unknown as Response);

    await streamChat('token', 'msg', undefined, (e) => events.push(e));

    expect(events).toHaveLength(1);
    expect(events[0].content).toBe('split');
  });

  it('sendsPOSTWithAuthHeaderAndBody', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      body: makeStream([]),
    } as unknown as Response);

    await streamChat('my-jwt', 'build me a thing', 'conv-99', () => {});

    expect(fetchSpy).toHaveBeenCalledWith(
      '/api/v1/chat/stream',
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer my-jwt',
        },
        body: JSON.stringify({ message: 'build me a thing', conversationId: 'conv-99' }),
      }),
    );
  });
});
