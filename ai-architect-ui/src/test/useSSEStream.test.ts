import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSSEStream } from '../hooks/useSSEStream';
import { useStore } from '../store/useStore';

// Mock streamChat
vi.mock('../api/chat', () => ({
  streamChat: vi.fn(),
}));

import { streamChat } from '../api/chat';
const mockStreamChat = vi.mocked(streamChat);

describe('useSSEStream', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStore.setState({
      token: 'jwt-token',
      conversationId: null,
      isStreaming: false,
      error: null,
      streamingText: '',
    });
  });

  it('setsErrorWhenNotAuthenticated', async () => {
    useStore.setState({ token: null });
    const { result } = renderHook(() => useSSEStream());

    await act(async () => {
      await result.current.send('hello');
    });

    expect(useStore.getState().error).toBe('Not authenticated');
    expect(mockStreamChat).not.toHaveBeenCalled();
  });

  it('callsStreamChatWithCorrectArgs', async () => {
    mockStreamChat.mockResolvedValue(undefined);
    useStore.setState({ token: 'jwt', conversationId: 'c1' });

    const { result } = renderHook(() => useSSEStream());

    await act(async () => {
      await result.current.send('build me a system');
    });

    expect(mockStreamChat).toHaveBeenCalledWith(
      'jwt',
      'build me a system',
      'c1',
      expect.any(Function),
      expect.any(AbortSignal),
    );
  });

  it('setsStreamingTrueWhileRunning', async () => {
    let resolveStream: () => void;
    mockStreamChat.mockImplementation(
      () => new Promise<void>((r) => (resolveStream = r)),
    );

    const { result } = renderHook(() => useSSEStream());

    let sendPromise: Promise<void>;
    act(() => {
      sendPromise = result.current.send('test');
    });

    expect(useStore.getState().isStreaming).toBe(true);

    await act(async () => {
      resolveStream!();
      await sendPromise!;
    });

    expect(useStore.getState().isStreaming).toBe(false);
  });

  it('setsErrorOnStreamFailure', async () => {
    mockStreamChat.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useSSEStream());

    await act(async () => {
      await result.current.send('test');
    });

    expect(useStore.getState().error).toBe('Network error');
  });

  it('abort_stopsStreaming', () => {
    const { result } = renderHook(() => useSSEStream());

    act(() => {
      result.current.abort();
    });

    expect(useStore.getState().isStreaming).toBe(false);
  });
});
