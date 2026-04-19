import type { ArchitectureOutput } from '../types/api';
import { authFetchJson } from './http';

const BASE = '/api/v1/sessions';

export async function getArchitecture(
  sessionId: string,
  token: string,
): Promise<ArchitectureOutput> {
  return authFetchJson<ArchitectureOutput>(
    `${BASE}/${sessionId}/architecture`,
    token,
  );
}

export async function getDiagram(
  sessionId: string,
  token: string,
): Promise<{ componentDiagram: string; sequenceDiagram: string }> {
  return authFetchJson<{ componentDiagram: string; sequenceDiagram: string }>(
    `${BASE}/${sessionId}/diagram`,
    token,
  );
}
