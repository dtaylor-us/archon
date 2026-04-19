import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MermaidDiagram } from '../components/MermaidDiagram';

// Mock mermaid since jsdom can't render SVG
vi.mock('mermaid', () => ({
  default: {
    initialize: vi.fn(),
    render: vi.fn(),
  },
}));

import mermaid from 'mermaid';
const mockRender = vi.mocked(mermaid.render);

describe('MermaidDiagram', () => {
  it('rendersEmptyState_whenChartIsEmpty', () => {
    render(<MermaidDiagram chart="" />);
    expect(screen.getByTestId('mermaid-empty')).toBeInTheDocument();
    expect(screen.getByText('No diagram available')).toBeInTheDocument();
  });

  it('rendersEmptyState_whenChartIsWhitespace', () => {
    render(<MermaidDiagram chart="   " />);
    expect(screen.getByTestId('mermaid-empty')).toBeInTheDocument();
  });

  it('rendersSVG_whenChartIsValid', async () => {
    mockRender.mockResolvedValue({ svg: '<svg>test</svg>', bindFunctions: vi.fn() } as never);

    render(<MermaidDiagram chart="graph LR; A-->B" id="test-diag" />);
    const container = screen.getByTestId('mermaid-container');
    expect(container).toBeInTheDocument();

    // Wait for async render
    await vi.waitFor(() => {
      expect(container.innerHTML).toContain('<svg>test</svg>');
    });
  });

  it('rendersErrorState_whenMermaidThrows', async () => {
    mockRender.mockRejectedValue(new Error('Parse error'));

    render(<MermaidDiagram chart="invalid chart" id="error-diag" />);

    const errorEl = await screen.findByTestId('mermaid-error');
    expect(errorEl).toBeInTheDocument();
    expect(errorEl.textContent).toContain('Parse error');
    // Should show raw source fallback
    expect(errorEl.textContent).toContain('invalid chart');
  });
});
