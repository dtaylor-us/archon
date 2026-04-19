import type { StageState } from '../types/api';
import { PIPELINE_STAGES } from '../types/api';

const STAGE_LABELS: Record<string, string> = {
  requirement_parsing: 'Requirement Parsing',
  requirement_challenge: 'Requirement Challenge',
  scenario_modeling: 'Scenario Modeling',
  characteristic_inference: 'Characteristic Inference',
  conflict_analysis: 'Conflict Analysis',
  architecture_generation: 'Architecture Generation',
  diagram_generation: 'Diagram Generation',
  trade_off_analysis: 'Trade-off Analysis',
  adl_generation: 'ADL Generation',
  weakness_analysis: 'Weakness Analysis',
  fmea_analysis: 'FMEA Analysis',
  architecture_review: 'Architecture Review',
};

function statusIcon(status: string): string {
  switch (status) {
    case 'complete':
      return '✓';
    case 'running':
      return '⟳';
    case 'error':
      return '✗';
    case 'aborted':
      return '–';
    default:
      return '○';
  }
}

function statusColor(status: string): string {
  switch (status) {
    case 'complete':
      return 'text-green-400';
    case 'running':
      return 'text-accent animate-pulse';
    case 'error':
      return 'text-red-400';
    case 'aborted':
      return 'text-gray-500';
    default:
      return 'text-gray-600';
  }
}

interface StageProgressProps {
  stages: StageState[];
}

export function StageProgress({ stages }: StageProgressProps) {
  const stageMap = new Map(stages.map((s) => [s.name, s]));

  return (
    <div className="space-y-1" data-testid="stage-progress">
      {PIPELINE_STAGES.map((name) => {
        const stage = stageMap.get(name);
        const status = stage?.status ?? 'pending';
        return (
          <div
            key={name}
            className={`flex items-center gap-2 text-sm font-mono ${statusColor(status)}`}
            data-testid={`stage-${name}`}
            data-status={status}
          >
            <span className="w-4 text-center text-xs">{statusIcon(status)}</span>
            <span className="truncate">{STAGE_LABELS[name] ?? name}</span>
          </div>
        );
      })}
    </div>
  );
}
