import axios from 'axios';

const apiBase = process.env.NEXT_PUBLIC_LCC_API_BASE_URL || 'http://localhost:8080';

export type ScanSummary = {
  id: string;
  project: string;
  status: 'pass' | 'warning' | 'violation' | 'running';
  violations: number;
  generatedAt: string;
  reportUrl?: string;
};

export type PolicySummary = {
  name: string;
  description: string;
  status: 'active' | 'draft';
  lastUpdated: string;
  disclaimer?: string;
};

export type PolicyContextSummary = {
  name: string;
  allow: string[];
  deny: string[];
  review: string[];
  dualLicensePreference: string;
};

export type PolicyDetail = PolicySummary & {
  contexts: PolicyContextSummary[];
};

export async function fetchDashboardSummary() {
  try {
    const response = await axios.get(`${apiBase}/dashboard`);
    return response.data;
  } catch (error) {
    const { mockSummary } = await import('./mock-data');
    return mockSummary;
  }
}

export async function fetchScanHistory() {
  try {
    const response = await axios.get(`${apiBase}/scans`);
    return response.data as ScanSummary[];
  } catch (error) {
    const { mockScans } = await import('./mock-data');
    return mockScans;
  }
}

export async function createScan(payload: { project: string; policy?: string }) {
  try {
    const response = await axios.post(`${apiBase}/scans`, payload);
    return response.data;
  } catch (error) {
    // When the API is not reachable we return a mock job id so the UI stays functional
    return { id: `job-${Date.now()}`, status: 'queued' };
  }
}

export async function fetchPolicies() {
  try {
    const response = await axios.get(`${apiBase}/policies`);
    return response.data as PolicySummary[];
  } catch (error) {
    const { mockPolicies } = await import('./mock-data');
    return mockPolicies;
  }
}

export async function fetchPolicy(name: string) {
  try {
    const response = await axios.get(`${apiBase}/policies/${name}`);
    return response.data as PolicyDetail;
  } catch (error) {
    const { mockPolicyDetails } = await import('./mock-data');
    return (mockPolicyDetails as Record<string, PolicyDetail | undefined>)[name] ?? null;
  }
}
