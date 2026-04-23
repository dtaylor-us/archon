/**
 * Home / orientation landing view for Archon.
 *
 * This view is static by design: it explains what Archon is, outlines the staged
 * pipeline, and provides a clear entry point into a new architecture session.
 */
export function HomeView({
  onStartSession,
}: {
  onStartSession: () => void;
}) {
  const PIPELINE = [
    { id: '01', name: 'Requirement parsing' },
    { id: '02', name: 'Requirement challenge' },
    { id: '03', name: 'Scenario modelling' },
    { id: '04', name: 'Characteristic inference' },
    { id: '04b', name: 'Tactics recommendation' },
    { id: '05', name: 'Conflict analysis' },
    { id: '06', name: 'Architecture generation' },
    { id: '06b', name: 'Buy vs build analysis' },
    { id: '07', name: 'Diagram generation' },
    { id: '08', name: 'Trade-off analysis' },
    { id: '09', name: 'ADL generation' },
    { id: '10', name: 'Weakness and FMEA' },
    { id: '12', name: 'Architecture review' },
  ] as const;

  const artifacts = [
    'Architecture diagrams (C4 container plus type-selected Mermaid)',
    'Trade-off record with documented decisions and scale testing',
    'ADL specification with executable governance rules',
    'FMEA risk analysis with RPN scores',
    'Architecture tactics report',
    'Governance score with confidence level and dimension breakdown',
    'Buy vs build decisions with named alternatives',
  ] as const;

  return (
    <div className="h-full overflow-y-auto" data-testid="home-view">
      <div className="max-w-5xl mx-auto p-6 md:p-10">
        <header
          className="archon-reveal"
          style={{ ['--reveal-delay' as any]: '0ms' }}
        >
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 shrink-0 bg-accent/90 rounded-2xl flex items-center justify-center shadow-sm">
              <svg
                className="w-6 h-6 text-white"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M3 21h18M3 10h18M12 3l9 7H3l9-7zM5 10v11m4-11v11m4-11v11m4-11v11" />
              </svg>
            </div>
            <div className="min-w-0 flex-1">
              <h1 className="text-2xl md:text-3xl font-semibold text-gray-900">
                Archon AI Architect
              </h1>
              <p className="text-[15px] text-gray-600 mt-2 leading-relaxed max-w-3xl">
                Archon is not a chatbot. It is a staged architecture reasoning pipeline that decomposes
                design thinking into a governed, inspectable process.
              </p>
              <div className="mt-5 flex flex-col sm:flex-row sm:items-center gap-2.5">
                <button
                  type="button"
                  onClick={onStartSession}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-accent text-white px-4 py-2.5 text-sm font-semibold hover:bg-accent-hover focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 transition-colors"
                  data-testid="home-start-session"
                >
                  Start an architecture session
                  <svg
                    className="w-4 h-4"
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M6 3l5 5-5 5" />
                  </svg>
                </button>
                <p className="text-[12px] text-gray-500">
                  No live data, no background calls — just the pipeline structure and what you’ll get out.
                </p>
              </div>
            </div>
          </div>
        </header>

        <div className="mt-10 grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-8">
          <main className="min-w-0 space-y-10">
            <section
              className="archon-reveal"
              style={{ ['--reveal-delay' as any]: '80ms' }}
              aria-labelledby="pipeline-title"
            >
              <div className="flex items-baseline justify-between gap-3">
                <h2 id="pipeline-title" className="text-lg font-bold text-gray-900">
                  Pipeline stages
                </h2>
                <p className="text-xs text-gray-500">
                  Monitored as a structured run, not a single response.
                </p>
              </div>

              <div className="mt-3 rounded-xl border border-gray-200 bg-white overflow-hidden">
                <ol className="divide-y divide-gray-100">
                  {PIPELINE.map((s) => {
                    const isGovernance = s.id === '12';
                    return (
                      <li
                        key={s.id}
                        className={`px-4 py-3 flex items-start justify-between gap-3 ${
                          isGovernance ? 'bg-accent/5' : ''
                        }`}
                        data-stage-id={s.id}
                      >
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-gray-900">
                            <span className="font-mono text-[12px] text-gray-500 mr-2">
                              {s.id}
                            </span>
                            {s.name}
                          </p>
                          {isGovernance && (
                            <p className="text-xs text-emerald-700 mt-1">
                              Governance stage — independent review and enforceability audit.
                            </p>
                          )}
                        </div>
                        {isGovernance && (
                          <span className="shrink-0 inline-flex items-center rounded-full bg-emerald-50 text-emerald-700 px-2.5 py-1 text-[11px] font-semibold">
                            Review
                          </span>
                        )}
                      </li>
                    );
                  })}
                </ol>
              </div>
            </section>

            <section
              className="archon-reveal"
              style={{ ['--reveal-delay' as any]: '140ms' }}
              aria-labelledby="capabilities-title"
            >
              <h2 id="capabilities-title" className="text-lg font-bold text-gray-900">
                Key capabilities
              </h2>

              <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                <article className="rounded-xl border border-gray-200 bg-white p-4">
                  <h3 className="text-sm font-semibold text-gray-900">Architecture style selection</h3>
                  <p className="text-sm text-gray-600 mt-1 leading-relaxed">
                    Scores all eight Mark Richards architecture styles against inferred characteristics, applies veto
                    rules, and never defaults to layered architecture without justification.
                  </p>
                </article>
                <article className="rounded-xl border border-gray-200 bg-white p-4">
                  <h3 className="text-sm font-semibold text-gray-900">Architecture tactics</h3>
                  <p className="text-sm text-gray-600 mt-1 leading-relaxed">
                    Recommends named tactics from the Bass, Clements, Kazman catalog for each quality attribute and
                    identifies which are already addressed and which are not.
                  </p>
                </article>
                <article className="rounded-xl border border-gray-200 bg-white p-4">
                  <h3 className="text-sm font-semibold text-gray-900">Buy vs build analysis</h3>
                  <p className="text-sm text-gray-600 mt-1 leading-relaxed">
                    Evaluates each architecture component for build, buy, or adopt. Names real products and open-source
                    projects and warns when recommendations conflict with stated preferences.
                  </p>
                </article>
                <article className="rounded-xl border border-gray-200 bg-white p-4">
                  <h3 className="text-sm font-semibold text-gray-900">Executable governance</h3>
                  <p className="text-sm text-gray-600 mt-1 leading-relaxed">
                    Generates Architecture Definition Language blocks following the Mark Richards ADL specification.
                    Rules compile to runnable ArchUnit, PyTestArch, and Semgrep tests.
                  </p>
                </article>
                <article className="rounded-xl border border-gray-200 bg-white p-4">
                  <h3 className="text-sm font-semibold text-gray-900">FMEA and weakness analysis</h3>
                  <p className="text-sm text-gray-600 mt-1 leading-relaxed">
                    Scores failure modes with Risk Priority Number, identifies cascading failures across service
                    boundaries, and classifies graceful versus catastrophic degradation.
                  </p>
                </article>
                <article className="rounded-xl border border-gray-200 bg-white p-4">
                  <h3 className="text-sm font-semibold text-gray-900">Architecture review agent</h3>
                  <p className="text-sm text-gray-600 mt-1 leading-relaxed">
                    A separate review agent challenges assumptions, stress-tests trade-offs, audits ADL enforceability,
                    and produces a governance score (0–100) across five dimensions.
                  </p>
                </article>
              </div>
            </section>

            <section
              className="archon-reveal"
              style={{ ['--reveal-delay' as any]: '200ms' }}
              aria-labelledby="difference-title"
            >
              <h2 id="difference-title" className="text-lg font-bold text-gray-900">
                Why it’s different
              </h2>

              <div className="mt-3 rounded-xl border border-gray-200 bg-white p-4">
                <p className="text-sm text-gray-700 leading-relaxed">
                  Most AI architecture tools produce one answer from one prompt with no intermediate reasoning and no
                  traceability. Archon runs a structured review process that produces inspectable intermediate artifacts
                  at every stage.
                </p>
                <ul className="mt-3 space-y-2 text-sm text-gray-700">
                  <li className="flex gap-2">
                    <span className="text-accent font-mono shrink-0" aria-hidden="true">—</span>
                    Requirements are challenged before design begins
                  </li>
                  <li className="flex gap-2">
                    <span className="text-accent font-mono shrink-0" aria-hidden="true">—</span>
                    Style is selected from a scored catalog with evidence, not chosen by default
                  </li>
                  <li className="flex gap-2">
                    <span className="text-accent font-mono shrink-0" aria-hidden="true">—</span>
                    Every finding traces back to a requirement, scenario, or characteristic
                  </li>
                  <li className="flex gap-2">
                    <span className="text-accent font-mono shrink-0" aria-hidden="true">—</span>
                    The architecture critiques itself before it is presented as final
                  </li>
                  <li className="flex gap-2">
                    <span className="text-accent font-mono shrink-0" aria-hidden="true">—</span>
                    Governance rules are executable, not just documented
                  </li>
                </ul>
              </div>
            </section>
          </main>

          <aside className="space-y-10">
            <section
              className="archon-reveal"
              style={{ ['--reveal-delay' as any]: '110ms' }}
              aria-labelledby="artifacts-title"
            >
              <h2 id="artifacts-title" className="text-lg font-bold text-gray-900">
                Output artifacts
              </h2>
              <div className="mt-3 rounded-xl border border-gray-200 bg-white p-4">
                <ul className="space-y-2 text-sm text-gray-700">
                  {artifacts.map((a) => (
                    <li key={a} className="flex gap-2">
                      <span className="text-gray-400 font-mono shrink-0" aria-hidden="true">
                        ✓
                      </span>
                      <span className="leading-relaxed">{a}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>

            <section
              className="archon-reveal"
              style={{ ['--reveal-delay' as any]: '170ms' }}
              aria-labelledby="start-title"
            >
              <h2 id="start-title" className="text-lg font-bold text-gray-900">
                Start a run
              </h2>
              <div className="mt-3 rounded-xl border border-gray-200 bg-gray-50 p-4">
                <p className="text-sm text-gray-700 leading-relaxed">
                  You’ll provide a requirements description. Archon will execute the full pipeline and stream each stage
                  as it completes.
                </p>
                <button
                  type="button"
                  onClick={onStartSession}
                  className="mt-4 w-full inline-flex items-center justify-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-semibold text-gray-800 hover:bg-gray-50 hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 transition-colors"
                >
                  Continue to chat
                  <span className="font-mono text-[12px] text-gray-500" aria-hidden="true">
                    /chat
                  </span>
                </button>
                <p className="text-[11px] text-gray-500 mt-2">
                  Tip: stage identifiers and artifacts are designed to be inspectable and exportable.
                </p>
              </div>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}

