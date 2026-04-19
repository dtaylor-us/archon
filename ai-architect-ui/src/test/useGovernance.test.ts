import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useGovernance } from '../hooks/useGovernance';
import { useStore } from '../store/useStore';

// Mock all API modules
vi.mock('../api/governance', () => ({
  getTradeOffs: vi.fn(),
  getAdl: vi.fn(),
  getWeaknesses: vi.fn(),
  getFmea: vi.fn(),
}));

import { getTradeOffs, getAdl, getWeaknesses, getFmea } from '../api/governance';

const mockGetTradeOffs = vi.mocked(getTradeOffs);
const mockGetAdl = vi.mocked(getAdl);
const mockGetWeaknesses = vi.mocked(getWeaknesses);
const mockGetFmea = vi.mocked(getFmea);

describe('useGovernance', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStore.setState({ token: 'jwt', conversationId: 'c1' });
  });

  it('fetchesAllGovernanceData_whenTokenAndConversationExist', async () => {
    mockGetTradeOffs.mockResolvedValue([]);
    mockGetAdl.mockResolvedValue({ document: 'doc', rules: [] });
    mockGetWeaknesses.mockResolvedValue({ weaknesses: [], summary: 'ok' });
    mockGetFmea.mockResolvedValue([]);

    const { result } = renderHook(() => useGovernance());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockGetTradeOffs).toHaveBeenCalledWith('c1', 'jwt');
    expect(result.current.adl?.document).toBe('doc');
    expect(result.current.error).toBeNull();
  });

  it('doesNotFetch_whenTokenIsNull', () => {
    useStore.setState({ token: null });

    renderHook(() => useGovernance());
    expect(mockGetTradeOffs).not.toHaveBeenCalled();
  });

  it('doesNotFetch_whenConversationIdIsNull', () => {
    useStore.setState({ conversationId: null });

    renderHook(() => useGovernance());
    expect(mockGetTradeOffs).not.toHaveBeenCalled();
  });

  it('setsError_whenFetchFails', async () => {
    mockGetTradeOffs.mockRejectedValue(new Error('API down'));
    mockGetAdl.mockRejectedValue(new Error('API down'));
    mockGetWeaknesses.mockRejectedValue(new Error('API down'));
    mockGetFmea.mockRejectedValue(new Error('API down'));

    const { result } = renderHook(() => useGovernance());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('API down');
  });
});
