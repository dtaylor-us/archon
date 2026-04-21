import { useEffect, useState, useRef } from 'react';
import { useStore } from './store/useStore';
import { ChatView } from './views/ChatView';
import { LoginView } from './views/LoginView';
import { ArchitectureView } from './views/ArchitectureView';
import { GovernanceView } from './views/GovernanceView';
import { StageProgress } from './components/StageProgress';
import { getSessionMessages, listSessions } from './api/sessions';
import type { SessionSummary } from './types/api';

type View = 'chat' | 'architecture' | 'governance';

const NAV_ITEMS: { key: View; label: string; icon: string }[] = [
  {
    key: 'chat',
    label: 'Chat',
    icon: 'M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z',
  },
  {
    key: 'architecture',
    label: 'Architecture',
    icon: 'M3 21h18M3 10h18M12 3l9 7H3l9-7zM5 10v11m4-11v11m4-11v11m4-11v11',
  },
  {
    key: 'governance',
    label: 'Governance',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
  },
];

export default function App() {
  const token = useStore((s) => s.token);
  const username = useStore((s) => s.username);
  const clearAuth = useStore((s) => s.clearAuth);
  const conversationId = useStore((s) => s.conversationId);
  const stages = useStore((s) => s.stages);
  const isStreaming = useStore((s) => s.isStreaming);
  const resetConversation = useStore((s) => s.resetConversation);
  const clearStages = useStore((s) => s.clearStages);
  const loadConversation = useStore((s) => s.loadConversation);
  const [activeView, setActiveView] = useState<View>('chat');
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [sessionsError, setSessionsError] = useState<string | null>(null);
  const [loadingSessionId, setLoadingSessionId] = useState<string | null>(null);

  const hasConversation = !!conversationId;
  const allStagesDone = stages.every((s) => s.status === 'complete' || s.status === 'error' || s.status === 'aborted');
  const wasAborted = !isStreaming && stages.some((s) => s.status === 'aborted');
  const hasActiveStages = stages.some((s) => s.status !== 'pending') && (isStreaming || !allStagesDone || wasAborted);

  /* Auto-dismiss the pipeline panel 3 s after abort or all stages done */
  const dismissTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!token) return;
    if (isStreaming) return;

    setSessionsLoading(true);
    setSessionsError(null);
    listSessions(token)
      .then((s) => {
        if (!cancelled) setSessions(s);
      })
      .catch((err) => {
        if (!cancelled) setSessionsError((err as Error).message ?? 'Failed to load history');
      })
      .finally(() => {
        if (!cancelled) setSessionsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token, conversationId, isStreaming]);

  useEffect(() => {
    if (dismissTimerRef.current) clearTimeout(dismissTimerRef.current);
    if (!isStreaming && allStagesDone && hasActiveStages) {
      dismissTimerRef.current = setTimeout(clearStages, 3000);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isStreaming, allStagesDone, hasActiveStages]);

  const handleLoadSession = async (sessionId: string) => {
    if (!token || isStreaming) return;
    setLoadingSessionId(sessionId);
    try {
      const msgs = await getSessionMessages(sessionId, token);
      // API returns messages newest-first (DESC); reverse to oldest-first so
      // the chat view renders chronologically with the latest at the bottom.
      loadConversation(sessionId, [...msgs].reverse());
      setActiveView('chat');
      setMobileDrawerOpen(false);
    } catch {
      // keep UI minimal: the view itself will surface any downstream errors
    } finally {
      setLoadingSessionId(null);
    }
  };

  /* ---------- Not authenticated → show login ---------- */
  if (!token) {
    return <LoginView />;
  }

  const activeViewLabel =
    activeView === 'chat'
      ? 'Chat'
      : activeView === 'architecture'
        ? 'Architecture'
        : 'Governance';

  return (
    <div className="flex h-full" data-testid="app-shell">
      {/* ── Desktop sidebar ── */}
      <aside className="hidden md:flex w-[280px] shrink-0 bg-sidebar flex-col" data-testid="sidebar">
        <div className="p-2">
          <button
            onClick={() => {
              resetConversation();
              setActiveView('chat');
            }}
            disabled={isStreaming}
            className="flex items-center gap-2 w-full border border-sidebar-border rounded-lg px-3 py-2.5 text-[13px] text-gray-200 hover:bg-sidebar-hover transition-colors disabled:opacity-40"
            data-testid="new-chat"
          >
            <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M8 3v10M3 8h10" />
            </svg>
            New chat
          </button>
        </div>

        <nav className="flex flex-col gap-0.5 px-2 mt-1">
          <button
            onClick={() => setActiveView('chat')}
            className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] transition-colors ${
              activeView === 'chat'
                ? 'bg-sidebar-hover text-white'
                : 'text-gray-400 hover:bg-sidebar-hover hover:text-gray-200'
            }`}
            data-testid="nav-chat"
          >
            <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
            </svg>
            Chat
          </button>
        </nav>

        {hasConversation && (
          <div className="mx-2 mt-2 rounded-lg border border-sidebar-border bg-sidebar-hover/30">
            <div className="px-3 pt-2 pb-1 flex items-center gap-1.5">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-accent shrink-0" />
              <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest truncate">
                Active session
              </span>
            </div>
            <nav className="flex flex-col gap-0.5 px-1 pb-1.5">
              {NAV_ITEMS.filter(({ key }) => key !== 'chat').map(({ key, label, icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveView(key)}
                  className={`flex items-center gap-2.5 rounded-md px-2 py-1.5 text-[13px] transition-colors ${
                    activeView === key
                      ? 'bg-sidebar-hover text-white'
                      : 'text-gray-400 hover:bg-sidebar-hover hover:text-gray-200'
                  }`}
                  data-testid={`nav-${key}`}
                >
                  <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d={icon} />
                  </svg>
                  {label}
                </button>
              ))}
            </nav>
          </div>
        )}

        <div className="mt-3 px-2 overflow-y-auto sidebar-scroll">
          <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest px-3 mb-1.5">History</h3>
          {sessionsLoading ? (
            <div className="px-3 py-2 text-[12px] text-gray-500">Loading…</div>
          ) : sessionsError ? (
            <div className="px-3 py-2 text-[12px] text-gray-500">{sessionsError}</div>
          ) : sessions.length === 0 ? (
            <div className="px-3 py-2 text-[12px] text-gray-500">No chats yet</div>
          ) : (
            <div className="flex flex-col gap-1">
              {sessions.map((s) => {
                const active = s.id === conversationId;
                const loading = loadingSessionId === s.id;
                return (
                  <button
                    key={s.id}
                    onClick={() => handleLoadSession(s.id)}
                    disabled={isStreaming || loading}
                    className={`text-left rounded-lg px-3 py-2 text-[12px] transition-colors relative ${
                      active
                        ? 'bg-accent/15 text-white ring-1 ring-accent/40'
                        : 'text-gray-400 hover:bg-sidebar-hover hover:text-gray-200'
                    } ${isStreaming || loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    title={s.title}
                    data-testid={`history-${s.id}`}
                  >
                    <div className="flex items-center gap-2">
                      {active && <span className="inline-block w-1.5 h-1.5 rounded-full bg-accent shrink-0" />}
                      <span className={`truncate ${active ? 'font-medium' : ''}`}>{s.title}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {hasActiveStages && (
          <div className="mt-3 px-2 overflow-y-auto sidebar-scroll">
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest px-3 mb-1.5">Pipeline</h3>
            <StageProgress stages={stages} />
          </div>
        )}

        <div className="flex-1" />

        <div className="border-t border-sidebar-border p-2">
          <div className="flex items-center gap-2.5 px-3 py-1.5 mb-1">
            <div className="w-6 h-6 shrink-0 rounded-full bg-accent/80 flex items-center justify-center">
              <span className="text-[10px] font-bold text-white">{(username ?? 'U')[0].toUpperCase()}</span>
            </div>
            <span className="text-[12px] text-gray-400 truncate">{username}</span>
          </div>
          <button
            onClick={() => {
              clearAuth();
              resetConversation();
            }}
            className="flex items-center gap-2.5 w-full rounded-lg px-3 py-2 text-[13px] text-gray-400 hover:bg-sidebar-hover hover:text-gray-200 transition-colors"
            data-testid="nav-logout"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
            </svg>
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Mobile drawer overlay ── */}
      {mobileDrawerOpen && (
        <div className="md:hidden fixed inset-0 z-50" role="dialog" aria-modal="true">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => setMobileDrawerOpen(false)}
            aria-label="Close menu"
          />
          <div className="absolute left-0 top-0 bottom-0 w-[86%] max-w-[360px] bg-sidebar flex flex-col">
            <div className="p-2 flex items-center justify-between">
              <div className="flex items-center gap-2 px-2 py-1">
                <span className="text-xs font-semibold text-gray-300">Menu</span>
                {hasConversation && <span className="text-[10px] text-gray-500 truncate">Active session</span>}
              </div>
              <button
                type="button"
                className="p-2 rounded-lg text-gray-300 hover:bg-sidebar-hover"
                onClick={() => setMobileDrawerOpen(false)}
                aria-label="Close menu"
              >
                <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M4 4l8 8M12 4l-8 8" />
                </svg>
              </button>
            </div>

            <div className="px-2 pb-2">
              <button
                onClick={() => {
                  resetConversation();
                  setActiveView('chat');
                  setMobileDrawerOpen(false);
                }}
                disabled={isStreaming}
                className="flex items-center gap-2 w-full border border-sidebar-border rounded-lg px-3 py-2.5 text-[13px] text-gray-200 hover:bg-sidebar-hover transition-colors disabled:opacity-40"
              >
                <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M8 3v10M3 8h10" />
                </svg>
                New chat
              </button>
            </div>

            {hasActiveStages && (
              <div className="px-2 pb-2">
                <div className="rounded-lg border border-sidebar-border bg-sidebar-hover/30 p-2">
                  <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest px-1 mb-1.5">Pipeline</h3>
                  <StageProgress stages={stages} />
                </div>
              </div>
            )}

            <div className="mt-1 px-2 overflow-y-auto sidebar-scroll">
              <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest px-3 mb-1.5">History</h3>
              {sessionsLoading ? (
                <div className="px-3 py-2 text-[12px] text-gray-500">Loading…</div>
              ) : sessionsError ? (
                <div className="px-3 py-2 text-[12px] text-gray-500">{sessionsError}</div>
              ) : sessions.length === 0 ? (
                <div className="px-3 py-2 text-[12px] text-gray-500">No chats yet</div>
              ) : (
                <div className="flex flex-col gap-1">
                  {sessions.map((s) => {
                    const active = s.id === conversationId;
                    const loading = loadingSessionId === s.id;
                    return (
                      <button
                        key={s.id}
                        onClick={() => handleLoadSession(s.id)}
                        disabled={isStreaming || loading}
                        className={`text-left rounded-lg px-3 py-2 text-[12px] transition-colors relative ${
                          active
                            ? 'bg-accent/15 text-white ring-1 ring-accent/40'
                            : 'text-gray-400 hover:bg-sidebar-hover hover:text-gray-200'
                        } ${isStreaming || loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                        title={s.title}
                      >
                        <div className="flex items-center gap-2">
                          {active && <span className="inline-block w-1.5 h-1.5 rounded-full bg-accent shrink-0" />}
                          <span className={`truncate ${active ? 'font-medium' : ''}`}>{s.title}</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="border-t border-sidebar-border p-2">
              <div className="flex items-center gap-2.5 px-3 py-1.5 mb-1">
                <div className="w-6 h-6 shrink-0 rounded-full bg-accent/80 flex items-center justify-center">
                  <span className="text-[10px] font-bold text-white">{(username ?? 'U')[0].toUpperCase()}</span>
                </div>
                <span className="text-[12px] text-gray-400 truncate">{username}</span>
              </div>
              <button
                onClick={() => {
                  clearAuth();
                  resetConversation();
                  setMobileDrawerOpen(false);
                }}
                className="flex items-center gap-2.5 w-full rounded-lg px-3 py-2 text-[13px] text-gray-400 hover:bg-sidebar-hover hover:text-gray-200 transition-colors"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
                </svg>
                Sign out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Main content ── */}
      <main className="flex-1 flex flex-col min-w-0 bg-white overflow-hidden">
        {/* Mobile top bar */}
        <div className="md:hidden border-b border-gray-100 bg-white">
          <div className="h-12 px-3 flex items-center justify-between gap-2">
            <button
              type="button"
              className="p-2 -ml-1 rounded-lg hover:bg-gray-50 active:bg-gray-100 transition-colors"
              onClick={() => setMobileDrawerOpen(true)}
              aria-label="Open menu"
            >
              <svg className="w-5 h-5 text-gray-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                <path d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            </button>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-gray-800 truncate">{activeViewLabel}</p>
              {hasConversation && (
                <p className="text-[11px] text-gray-500 truncate">
                  Session loaded
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={() => {
                resetConversation();
                setActiveView('chat');
              }}
              disabled={isStreaming}
              className="text-xs font-medium rounded-lg px-2.5 py-1.5 border border-gray-200 text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              New
            </button>
          </div>
        </div>

        {/* Content (leave space for fixed mobile bottom nav) */}
        <div className="flex-1 min-h-0 pb-[calc(3.5rem+env(safe-area-inset-bottom))] md:pb-0">
          {activeView === 'chat' && <ChatView />}
          {activeView === 'architecture' && (
            <div className="h-full overflow-y-auto">
              <div className="max-w-5xl mx-auto"><ArchitectureView /></div>
            </div>
          )}
          {activeView === 'governance' && (
            <div className="h-full overflow-y-auto">
              <div className="max-w-5xl mx-auto"><GovernanceView /></div>
            </div>
          )}
        </div>

        {/* Mobile bottom nav */}
        <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 border-t border-gray-100 bg-white/95 backdrop-blur pb-[env(safe-area-inset-bottom)]">
          <div className="grid grid-cols-3 h-14">
            {NAV_ITEMS.map(({ key, label, icon }) => {
              const active = activeView === key;
              const disabled = (key !== 'chat') && !hasConversation;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setActiveView(key)}
                  disabled={disabled}
                  className={`flex flex-col items-center justify-center gap-1 text-[11px] transition-colors ${
                    active ? 'text-accent' : 'text-gray-500'
                  } ${disabled ? 'opacity-40' : 'hover:bg-gray-50 active:bg-gray-100'}`}
                  aria-current={active ? 'page' : undefined}
                  data-testid={`mobile-nav-${key}`}
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                    <path d={icon} />
                  </svg>
                  <span className="leading-none">{label}</span>
                </button>
              );
            })}
          </div>
        </nav>
      </main>
    </div>
  );
}
