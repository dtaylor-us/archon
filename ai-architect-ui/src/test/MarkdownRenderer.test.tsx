import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MarkdownRenderer } from '../components/MarkdownRenderer';

describe('MarkdownRenderer', () => {
  it('rendersEmptyState_whenContentIsEmpty', () => {
    render(<MarkdownRenderer content="" />);
    expect(screen.getByTestId('markdown-empty')).toBeInTheDocument();
    expect(screen.getByText('No content available')).toBeInTheDocument();
  });

  it('rendersEmptyState_whenContentIsWhitespace', () => {
    render(<MarkdownRenderer content="   " />);
    expect(screen.getByTestId('markdown-empty')).toBeInTheDocument();
  });

  it('rendersMarkdownContent', () => {
    render(<MarkdownRenderer content="# Hello World" />);
    expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('rendersBoldText', () => {
    render(<MarkdownRenderer content="This is **bold** text" />);
    const bold = screen.getByText('bold');
    expect(bold.tagName.toLowerCase()).toBe('strong');
  });
});
