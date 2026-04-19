import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ArchitectureView } from '../views/ArchitectureView';

let architectureState: Record<string, unknown>;

vi.mock('../hooks/useArchitecture', () => ({
  useArchitecture: () => architectureState,
}));

// Mock MermaidDiagram to avoid mermaid import in jsdom
vi.mock('../components/MermaidDiagram', () => ({
  MermaidDiagram: ({ chart }: { chart: string }) => (
    <div data-testid="mock-mermaid">{chart}</div>
  ),
}));

describe('ArchitectureView', () => {
  beforeEach(() => {
    architectureState = {
      architecture: null,
      loading: false,
      error: null,
    };
  });

  it('rendersLoadingState', () => {
    architectureState.loading = true;
    render(<ArchitectureView />);
    expect(screen.getByTestId('architecture-loading')).toBeInTheDocument();
  });

  it('rendersErrorState', () => {
    architectureState.error = 'API failed';
    render(<ArchitectureView />);
    expect(screen.getByTestId('architecture-error')).toHaveTextContent('API failed');
  });

  it('rendersEmptyState', () => {
    render(<ArchitectureView />);
    expect(screen.getByTestId('architecture-empty')).toBeInTheDocument();
  });

  it('rendersArchitectureData', () => {
    architectureState.architecture = {
      conversationId: 'c1',
      style: 'Microservices',
      components: [
        { name: 'API Gateway', responsibility: 'Routing', technology: 'Spring' },
        { name: 'Auth Service', responsibility: 'Auth', technology: 'Keycloak' },
      ],
      interactions: [
        { from: 'API Gateway', to: 'Auth Service', protocol: 'HTTP', purpose: 'Auth' },
      ],
      componentDiagram: 'graph LR; A-->B',
      sequenceDiagram: 'sequenceDiagram; A->>B: call',
    };

    render(<ArchitectureView />);
    expect(screen.getByTestId('architecture-view')).toBeInTheDocument();
    expect(screen.getByText('Microservices')).toBeInTheDocument();
    expect(screen.getAllByText('API Gateway').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Auth Service').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('HTTP')).toBeInTheDocument();
    // Mermaid diagrams rendered
    expect(screen.getAllByTestId('mock-mermaid')).toHaveLength(2);
  });
});
