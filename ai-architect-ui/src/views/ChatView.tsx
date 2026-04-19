import { useState, useRef, useEffect, type FormEvent } from 'react';
import { useConversation } from '../hooks/useConversation';
import { MarkdownRenderer } from '../components/MarkdownRenderer';

const EXAMPLES = [
  'Design a payment processing system with Stripe integration',
  'Build a real-time collaborative document editor',
  'Create a microservices e-commerce platform',
  'Design a video streaming service like Netflix',
];

export function ChatView() {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const {
    messages,
    streamingText,
    isStreaming,
    error,
    sendMessage,
    abort,
    resetConversation,
  } = useConversation();

  /* Auto-scroll on new content */
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingText]);

  /* Auto-resize textarea */
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [input]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    const msg = input.trim();
    setInput('');
    await sendMessage(msg);
  };

  const handleExample = async (example: string) => {
    if (isStreaming) return;
    await sendMessage(example);
  };

  const handleReset = () => {
    resetConversation();
  };

  const hasContent = messages.length > 0 || !!streamingText;

  return (
    <div className="flex flex-col h-full" data-testid="chat-view">
      {/* ── Messages area ── */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {!hasContent ? (
          /* Welcome / empty state */
          <div className="flex flex-col items-center justify-center h-full px-4" data-testid="chat-empty">
            <div className="max-w-2xl text-center space-y-6">
              <div className="w-14 h-14 mx-auto bg-accent/90 rounded-2xl flex items-center justify-center shadow-sm">
                <svg className="w-7 h-7 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 21h18M3 10h18M12 3l9 7H3l9-7zM5 10v11m4-11v11m4-11v11m4-11v11" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-semibold text-gray-800">Archon</h1>
                <p className="text-[15px] text-gray-500 mt-2">
                  Describe your system architecture needs and get AI-powered recommendations tailored to your requirements.
                </p>
              </div>
              <div className="grid sm:grid-cols-2 gap-2 text-left">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    onClick={() => handleExample(ex)}
                    className="border border-gray-200 rounded-xl px-4 py-3 text-[13px] text-gray-600 hover:bg-gray-50 hover:border-gray-300 transition-colors text-left leading-relaxed"
                    data-testid="example-prompt"
                  >
                    &ldquo;{ex}&rdquo;
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Conversation */
          <div className="max-w-3xl mx-auto w-full px-4 py-6 space-y-6" data-testid="chat-messages">
            {/* Transcript */}
            {messages.map((m, idx) => {
              const key = m.id ?? `${m.role}-${idx}`;

              if (m.role === 'USER') {
                return (
                  <div className="flex gap-3" data-testid="user-message" key={key}>
                    <div className="w-7 h-7 shrink-0 rounded-full bg-gray-800 flex items-center justify-center mt-0.5">
                      <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 12c2.7 0 5-2.3 5-5s-2.3-5-5-5-5 2.3-5 5 2.3 5 5 5zm0 2c-3.3 0-10 1.7-10 5v2h20v-2c0-3.3-6.7-5-10-5z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-gray-800 mb-1">You</p>
                      <p className="text-[15px] text-gray-700 leading-relaxed">{m.content}</p>
                    </div>
                  </div>
                );
              }

              return (
                <div className="flex gap-3" data-testid="assistant-message" key={key}>
                  <div className="w-7 h-7 shrink-0 rounded-full bg-accent flex items-center justify-center mt-0.5">
                    <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3 21h18M3 10h18M12 3l9 7H3l9-7zM5 10v11m4-11v11m4-11v11m4-11v11" />
                    </svg>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-gray-800 mb-1">Archon</p>
                    <MarkdownRenderer content={m.content} />
                  </div>
                </div>
              );
            })}

            {/* Error */}
            {error && (
              <div className="flex items-start gap-2 bg-red-50 border border-red-100 rounded-xl px-4 py-3" data-testid="chat-error">
                <svg className="w-4 h-4 text-red-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* In-flight assistant response */}
            {isStreaming && (
              <div className="flex gap-3" data-testid="assistant-message">
                <div className="w-7 h-7 shrink-0 rounded-full bg-accent flex items-center justify-center mt-0.5">
                  <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 21h18M3 10h18M12 3l9 7H3l9-7zM5 10v11m4-11v11m4-11v11m4-11v11" />
                  </svg>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold text-gray-800 mb-1">Archon</p>
                  {streamingText ? (
                    <>
                      <MarkdownRenderer content={streamingText} />
                      <span className="inline-block w-1.5 h-4 bg-gray-800 animate-pulse align-text-bottom ml-0.5" />
                    </>
                  ) : (
                    <div className="flex items-center gap-1.5 py-2">
                      <div className="w-2 h-2 bg-accent rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-accent rounded-full animate-bounce [animation-delay:150ms]" />
                      <div className="w-2 h-2 bg-accent rounded-full animate-bounce [animation-delay:300ms]" />
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Input area ── */}
      <div className="border-t border-gray-100 bg-white px-4 pb-4 pt-3">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div className="flex items-end border border-gray-200 rounded-2xl shadow-sm focus-within:border-gray-300 focus-within:shadow-md transition-all bg-white">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Describe your system requirements…"
              rows={1}
              className="flex-1 resize-none border-0 bg-transparent px-4 py-3.5 text-[15px] text-gray-800 placeholder:text-gray-400 focus:outline-none max-h-[200px]"
              data-testid="chat-input"
              disabled={isStreaming}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            <div className="flex items-center gap-1.5 pr-2 pb-2">
              {isStreaming ? (
                <button
                  type="button"
                  onClick={abort}
                  className="p-2 rounded-lg bg-gray-800 text-white hover:bg-gray-700 transition-colors"
                  data-testid="chat-abort"
                  title="Stop generating"
                >
                  <svg className="w-4 h-4" viewBox="0 0 16 16" fill="currentColor">
                    <rect x="3" y="3" width="10" height="10" rx="1" />
                  </svg>
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!input.trim()}
                  className="p-2 rounded-lg bg-gray-800 text-white hover:bg-gray-700 disabled:bg-gray-200 disabled:text-gray-400 transition-colors"
                  data-testid="chat-submit"
                  title="Send message"
                >
                  <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M8 12V4M4 8l4-4 4 4" />
                  </svg>
                </button>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between mt-2 px-1">
            <p className="text-[11px] text-gray-400">
              Archon may produce inaccurate designs. Verify critical decisions.
            </p>
            <button
              type="button"
              onClick={handleReset}
              disabled={isStreaming}
              className="text-[11px] text-gray-400 hover:text-gray-600 disabled:opacity-50 transition-colors"
              data-testid="chat-reset"
            >
              New chat
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
