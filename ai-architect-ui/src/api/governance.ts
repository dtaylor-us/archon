import type {
  TradeOffDecision,
  AdlDocument,
  WeaknessReport,
  FmeaEntry,
  GovernanceReport,
} from '../types/api';
import { authFetchJson } from './http';

const BASE = '/api/v1/sessions';

export async function getTradeOffs(
  sessionId: string,
  token: string,
): Promise<TradeOffDecision[]> {
  return authFetchJson<TradeOffDecision[]>(
    `${BASE}/${sessionId}/trade-offs`,
    token,
  );
}

export async function getAdl(
  sessionId: string,
  token: string,
): Promise<AdlDocument> {
  return authFetchJson<AdlDocument>(`${BASE}/${sessionId}/adl`, token);
}

export async function getAdlHard(
  sessionId: string,
  token: string,
): Promise<AdlDocument> {
  return authFetchJson<AdlDocument>(`${BASE}/${sessionId}/adl/hard`, token);
}

export async function getAdlByCategory(
  sessionId: string,
  category: string,
  token: string,
): Promise<AdlDocument> {
  return authFetchJson<AdlDocument>(
    `${BASE}/${sessionId}/adl/${category}`,
    token,
  );
}

export async function getWeaknesses(
  sessionId: string,
  token: string,
): Promise<WeaknessReport> {
  return authFetchJson<WeaknessReport>(
    `${BASE}/${sessionId}/weaknesses`,
    token,
  );
}

export async function getFmea(
  sessionId: string,
  token: string,
): Promise<FmeaEntry[]> {
  return authFetchJson<FmeaEntry[]>(`${BASE}/${sessionId}/fmea`, token);
}

export async function getFmeaRisks(
  sessionId: string,
  token: string,
): Promise<FmeaEntry[]> {
  return authFetchJson<FmeaEntry[]>(`${BASE}/${sessionId}/fmea-risks`, token);
}

export async function getGovernanceReport(
  sessionId: string,
  token: string,
): Promise<GovernanceReport> {
  return authFetchJson<GovernanceReport>(
    `${BASE}/${sessionId}/governance`,
    token,
  );
}
