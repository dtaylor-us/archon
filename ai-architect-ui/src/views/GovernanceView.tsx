import { useState } from 'react';
import { useGovernance } from '../hooks/useGovernance';
import { MarkdownRenderer } from '../components/MarkdownRenderer';
import { SeverityGrid } from '../components/SeverityGrid';
import type { Weakness } from '../types/api';

function severityBadgeClass(w: Weakness): string {
  if (w.severity >= 8) return 'bg-red-100 text-red-700';
  if (w.severity >= 6) return 'bg-orange-100 text-orange-700';
  if (w.severity >= 4) return 'bg-yellow-100 text-yellow-700';
  return 'bg-green-100 text-green-700';
}

type Tab = 'trade-offs' | 'adl' | 'weaknesses' | 'fmea';

export function GovernanceView() {
  const [activeTab, setActiveTab] = useState<Tab>('trade-offs');
  const { tradeOffs, adl, weaknesses, fmea, loading, error } = useGovernance();

  const tabs: { key: Tab; label: string }[] = [
    { key: 'trade-offs', label: 'Trade-offs' },
    { key: 'adl', label: 'ADL' },
    { key: 'weaknesses', label: 'Weaknesses' },
    { key: 'fmea', label: 'FMEA' },
  ];

  if (loading) {
    return (
      <div className="p-6 text-gray-500" data-testid="governance-loading">
        Loading governance data…
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6" data-testid="governance-error">
        <div className="bg-red-50 border border-red-100 rounded-xl px-4 py-3">
          <p className="text-sm font-semibold text-red-800">Unable to load governance</p>
          <p className="text-sm text-red-700 mt-1">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6" data-testid="governance-view">
      {/* Tab bar */}
      <div className="flex border-b border-gray-200 mb-4">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`px-4 py-2 text-sm font-medium -mb-px ${
              activeTab === key
                ? 'border-b-2 border-accent text-accent'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            data-testid={`tab-${key}`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'trade-offs' && (
        <div data-testid="panel-trade-offs">
          {tradeOffs.length === 0 ? (
            <p className="text-gray-400 italic">No trade-off decisions available</p>
          ) : (
            <div className="space-y-3">
              {tradeOffs.map((t) => (
                <div
                  key={t.decision_id}
                  className="border border-gray-200 rounded p-4 bg-white"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-sm">{t.decision}</h3>
                    <span className={`text-xs rounded px-2 py-0.5 font-medium shrink-0 ${
                      t.confidence === 'high' ? 'bg-green-100 text-green-700' :
                      t.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>{t.confidence}</span>
                  </div>
                  <div className="mt-2 text-xs text-gray-600 space-y-1">
                    <p>
                      <span className="font-medium text-green-700">Optimises:</span>{' '}
                      {(t.optimises_characteristics ?? []).join(', ')}
                    </p>
                    <p>
                      <span className="font-medium text-red-700">Sacrifices:</span>{' '}
                      {(t.sacrifices_characteristics ?? []).join(', ')}
                    </p>
                    <p>
                      <span className="font-medium">Recommendation:</span>{' '}
                      {t.recommendation}
                    </p>
                    <p>
                      <span className="font-medium">Context dependency:</span>{' '}
                      {t.context_dependency}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'adl' && (
        <div data-testid="panel-adl">
          {!adl ? (
            <p className="text-gray-400 italic">No ADL document available</p>
          ) : (
            <div className="space-y-4">
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <MarkdownRenderer content={adl.document} />
              </div>
              <h3 className="text-sm font-semibold">
                Rules ({adl.rules.length})
              </h3>
              <div className="space-y-2">
                {adl.rules.map((r, i) => (
                  <div
                    key={i}
                    className="border border-gray-200 rounded p-3 text-xs bg-gray-50"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-emerald-700 uppercase">{r.category}</span>
                      <span className="font-mono text-gray-400">{r.rule_id}</span>
                      <span className="font-medium text-purple-700">{r.subject}</span>
                    </div>
                    <p className="text-gray-700">{r.statement}</p>
                    {r.rationale && (
                      <p className="text-gray-500 mt-1 italic">{r.rationale}</p>
                    )}
                    {r.validation_hint?.pseudo_code && (
                      <pre className="whitespace-pre-wrap mt-1 text-gray-500 text-xs bg-gray-100 rounded p-1 overflow-x-auto">
                        {r.validation_hint.pseudo_code}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'weaknesses' && (
        <div data-testid="panel-weaknesses">
          {!weaknesses || weaknesses.weaknesses.length === 0 ? (
            <p className="text-gray-400 italic">No weaknesses identified</p>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-gray-700 bg-gray-50 rounded p-3">
                {weaknesses.summary}
              </p>
              <div className="space-y-3">
                {weaknesses.weaknesses.map((w) => (
                  <div
                    key={w.id}
                    className="border border-gray-200 rounded p-3 bg-white"
                  >
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs text-gray-500">
                        {w.id}
                      </span>
                      <h3 className="font-semibold text-sm">{w.title}</h3>
                      <span className={`text-xs rounded px-2 py-0.5 font-medium ${
                        severityBadgeClass(w)
                      }`}>
                        Severity {w.severity}/10
                      </span>
                      {w.category && (
                        <span className="text-xs rounded px-2 py-0.5 font-medium bg-gray-100 text-gray-600">
                          {w.category}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mt-1">
                      {w.description}
                    </p>
                    <p className="text-xs mt-1">
                      <span className="font-medium">Affected:</span>{' '}
                      {w.component_affected}
                    </p>
                    <p className="text-xs mt-1">
                      <span className="font-medium">Mitigation:</span>{' '}
                      {w.mitigation}
                    </p>
                    {w.effort_to_fix && (
                      <p className="text-xs mt-1">
                        <span className="font-medium">Effort:</span>{' '}
                        {w.effort_to_fix}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'fmea' && (
        <div data-testid="panel-fmea">
          <SeverityGrid entries={fmea} />
        </div>
      )}
    </div>
  );
}
