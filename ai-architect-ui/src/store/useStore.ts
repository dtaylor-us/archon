import { create } from 'zustand';
import type {
  AgentEvent,
  ChatMessage,
  StageName,
  StageState,
} from '../types/api';
import { PIPELINE_STAGES as STAGES } from '../types/api';

/* ── Slice types ─────────────────────────────────── */

interface AuthSlice {
  token: string | null;
  username: string | null;
  setAuth: (token: string, username: string) => void;
  clearAuth: () => void;
}

interface ConversationSlice {
  conversationId: string | null;
  messages: ChatMessage[];
  streamingText: string;
  isStreaming: boolean;
  error: string | null;
  stages: StageState[];
  /** Incremented each time a COMPLETE event is received — lets hooks re-fetch. */
  pipelineVersion: number;
  setConversationId: (id: string) => void;
  loadConversation: (id: string, messages: ChatMessage[]) => void;
  setStreaming: (v: boolean) => void;
  setError: (msg: string | null) => void;
  beginUserTurn: (content: string) => void;
  appendChunk: (text: string) => void;
  handleEvent: (event: AgentEvent) => void;
  abortStreaming: () => void;
  clearStages: () => void;
  resetConversation: () => void;
}

export type AppStore = AuthSlice & ConversationSlice;

function initialStages(): StageState[] {
  return (STAGES as readonly StageName[]).map((name) => ({
    name,
    status: 'pending',
  }));
}

export const useStore = create<AppStore>((set, get) => ({
  /* ── Auth ─────────────────────────────────────── */
  token: null,
  username: null,
  setAuth: (token, username) => set({ token, username }),
  clearAuth: () => set({ token: null, username: null }),

  /* ── Conversation ─────────────────────────────── */
  conversationId: null,
  messages: [],
  streamingText: '',
  isStreaming: false,
  error: null,
  stages: initialStages(),
  pipelineVersion: 0,

  setConversationId: (id) => set({ conversationId: id }),
  loadConversation: (id, messages) =>
    set({
      conversationId: id,
      messages,
      streamingText: '',
      isStreaming: false,
      error: null,
      stages: initialStages(),
    }),
  setStreaming: (v) => set({ isStreaming: v }),
  setError: (msg) => set({ error: msg }),
  beginUserTurn: (content) =>
    set((s) => ({
      messages: [...s.messages, { role: 'USER', content }],
      streamingText: '',
      error: null,
      stages: initialStages(),
    })),
  appendChunk: (text) =>
    set((s) => ({ streamingText: s.streamingText + text })),

  abortStreaming: () =>
    set((s) => ({
      isStreaming: false,
      stages: s.stages.map((st) =>
        st.status === 'running' ? { ...st, status: 'aborted' } : st,
      ),
      messages:
        s.streamingText.trim().length > 0
          ? [...s.messages, { role: 'ASSISTANT', content: s.streamingText }]
          : s.messages,
      streamingText: '',
    })),

  clearStages: () => set({ stages: initialStages() }),

  handleEvent: (event: AgentEvent) => {
    const state = get();

    switch (event.type) {
      case 'CHUNK':
        if (event.content) {
          set({ streamingText: state.streamingText + event.content });
        }
        break;

      case 'STAGE_START':
        if (event.stage) {
          set({
            stages: state.stages.map((s) =>
              s.name === event.stage ? { ...s, status: 'running' } : s,
            ),
          });
        }
        break;

      case 'STAGE_COMPLETE':
        if (event.stage) {
          set({
            stages: state.stages.map((s) =>
              s.name === event.stage
                ? { ...s, status: 'complete', payload: event.payload }
                : s,
            ),
          });
        }
        break;

      case 'COMPLETE':
        set((s) => ({
          isStreaming: false,
          conversationId:
            event.conversationId ??
            (event.payload?.conversationId as string) ??
            s.conversationId,
          messages:
            s.streamingText.trim().length > 0
              ? [...s.messages, { role: 'ASSISTANT', content: s.streamingText }]
              : s.messages,
          streamingText: '',
          pipelineVersion: s.pipelineVersion + 1,
        }));
        break;

      case 'RE_ITERATE':
        // Reset stages to pending for a new iteration pass
        set({
          stages: initialStages(),
        });
        break;

      case 'ERROR':
        set({
          isStreaming: false,
          error: event.content ?? 'An unknown error occurred',
          stages: state.stages.map((s) =>
            s.status === 'running' ? { ...s, status: 'error' } : s,
          ),
        });
        break;

      // handleEvent never throws for unknown event types
      default:
        break;
    }
  },

  resetConversation: () =>
    set({
      conversationId: null,
      messages: [],
      streamingText: '',
      isStreaming: false,
      error: null,
      stages: initialStages(),
      pipelineVersion: 0,
    }),
}));
