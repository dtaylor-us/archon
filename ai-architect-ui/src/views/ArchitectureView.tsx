import { useArchitecture } from '../hooks/useArchitecture';
import { MermaidDiagram } from '../components/MermaidDiagram';

export function ArchitectureView() {
  const { architecture, loading, error } = useArchitecture();

  if (loading) {
    return (
      <div className="p-6 text-gray-500" data-testid="architecture-loading">
        Loading architecture…
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6" data-testid="architecture-error">
        <div className="bg-red-50 border border-red-100 rounded-xl px-4 py-3">
          <p className="text-sm font-semibold text-red-800">Unable to load architecture</p>
          <p className="text-sm text-red-700 mt-1">{error}</p>
        </div>
      </div>
    );
  }

  if (!architecture) {
    return (
      <div className="p-6 text-gray-400 italic" data-testid="architecture-empty">
        No architecture data yet. Run the pipeline first.
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8" data-testid="architecture-view">
      {/* Summary */}
      <section>
        <h2 className="text-lg font-bold text-gray-800 mb-2">
          Architecture Style
        </h2>
        <p className="text-sm text-gray-700 bg-gray-50 rounded p-3">
          {architecture.style}
        </p>
      </section>

      {/* Components */}
      <section>
        <h2 className="text-lg font-bold text-gray-800 mb-2">Components</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {architecture.components.map((c) => (
            <div
              key={c.name}
              className="border border-gray-200 rounded p-3 bg-white"
            >
              <h3 className="font-semibold text-sm">{c.name}</h3>
              <p className="text-xs text-gray-600 mt-1">{c.responsibility}</p>
              <span className="inline-block mt-1 text-xs bg-emerald-50 text-emerald-700 rounded px-2 py-0.5">
                {c.technology}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Interactions */}
      <section>
        <h2 className="text-lg font-bold text-gray-800 mb-2">Interactions</h2>
        <div className="overflow-x-auto">
          <table className="text-sm w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="border p-2 text-left">From</th>
                <th className="border p-2 text-left">To</th>
                <th className="border p-2 text-left">Protocol</th>
                <th className="border p-2 text-left">Purpose</th>
              </tr>
            </thead>
            <tbody>
              {architecture.interactions.map((i, idx) => (
                <tr key={idx} className="odd:bg-white even:bg-gray-50">
                  <td className="border p-2">{i.from}</td>
                  <td className="border p-2">{i.to}</td>
                  <td className="border p-2 font-mono text-xs">{i.protocol}</td>
                  <td className="border p-2">{i.purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Diagrams */}
      <section>
        <h2 className="text-lg font-bold text-gray-800 mb-2">
          Component Diagram
        </h2>
        <MermaidDiagram
          chart={architecture.componentDiagram}
          id="component-diagram"
        />
      </section>

      <section>
        <h2 className="text-lg font-bold text-gray-800 mb-2">
          Sequence Diagram
        </h2>
        <MermaidDiagram
          chart={architecture.sequenceDiagram}
          id="sequence-diagram"
        />
      </section>
    </div>
  );
}
