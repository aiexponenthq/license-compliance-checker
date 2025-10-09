export const mockSummary = {
  totalViolations: 4,
  totalProjects: 12,
  highRiskProjects: 2,
  pendingScans: 3,
  licenseDistribution: [
    { license: 'MIT', count: 120 },
    { license: 'Apache-2.0', count: 80 },
    { license: 'GPL-3.0', count: 6 },
    { license: 'Unknown', count: 10 },
  ],
  trend: [
    { month: 'Jan', violations: 12 },
    { month: 'Feb', violations: 9 },
    { month: 'Mar', violations: 7 },
    { month: 'Apr', violations: 11 },
    { month: 'May', violations: 6 },
    { month: 'Jun', violations: 4 },
  ],
};

export const mockScans = [
  {
    id: 'scan-001',
    project: 'payments-service',
    status: 'violation',
    violations: 3,
    generatedAt: '2025-10-01T08:30:00Z',
    reportUrl: '#',
  },
  {
    id: 'scan-002',
    project: 'customer-portal',
    status: 'warning',
    violations: 1,
    generatedAt: '2025-09-27T14:45:00Z',
    reportUrl: '#',
  },
  {
    id: 'scan-003',
    project: 'ml-model-serving',
    status: 'pass',
    violations: 0,
    generatedAt: '2025-09-25T11:20:00Z',
    reportUrl: '#',
  },
  {
    id: 'scan-004',
    project: 'mobile-app',
    status: 'running',
    violations: 0,
    generatedAt: '2025-10-08T12:00:00Z',
  },
];

export const mockPolicies = [
  {
    name: 'permissive',
    description: 'Allows permissive licenses and blocks copyleft.',
    status: 'active',
    lastUpdated: '2025-09-20',
    disclaimer: 'Automated outcome only—confirm with legal counsel before release.',
  },
  {
    name: 'mobile-app',
    description: 'Restrict GPL-family licenses for mobile deployments.',
    status: 'draft',
    lastUpdated: '2025-09-15',
    disclaimer: 'Tailored for app store distribution; counsel review required.',
  },
];

export const mockPolicyDetails = {
  permissive: {
    name: 'permissive',
    description: 'Allows permissive licenses and blocks copyleft.',
    status: 'active',
    lastUpdated: '2025-09-20',
    disclaimer: 'Automated outcome only—confirm with legal counsel before release.',
    contexts: [
      {
        name: 'internal',
        allow: ['MIT', 'Apache-2.0', 'BSD-*', 'ISC'],
        deny: ['SSPL-1.0'],
        review: ['GPL-*', 'AGPL-*'],
        dualLicensePreference: 'most_permissive',
      },
      {
        name: 'saas',
        allow: ['MIT', 'Apache-2.0', 'BSD-*'],
        deny: ['SSPL-1.0', 'AGPL-*', 'GPL-3.0'],
        review: ['LGPL-*', 'MPL-*'],
        dualLicensePreference: 'avoid_copyleft',
      },
    ],
  },
  'mobile-app': {
    name: 'mobile-app',
    description: 'Restrict GPL-family licenses for mobile deployments.',
    status: 'draft',
    lastUpdated: '2025-09-15',
    disclaimer: 'Tailored for app store distribution; counsel review required.',
    contexts: [
      {
        name: 'app-store',
        allow: ['MIT', 'Apache-2.0', 'BSD-*', 'CC-BY-4.0'],
        deny: ['GPL-3.0', 'AGPL-3.0', 'SSPL-1.0'],
        review: ['LGPL-*', 'MPL-2.0'],
        dualLicensePreference: 'avoid_copyleft',
      },
      {
        name: 'enterprise',
        allow: ['MIT', 'Apache-2.0', 'BSD-*', 'LGPL-*'],
        deny: ['SSPL-1.0'],
        review: ['GPL-*', 'AGPL-*'],
        dualLicensePreference: 'most_permissive',
      },
    ],
  },
} as const;
