'use client';

import { useQuery } from '@tanstack/react-query';
import { LayoutShell } from '../components/LayoutShell';
import { SummaryCards } from '../components/SummaryCards';
import { LicenseDistribution } from '../components/LicenseDistribution';
import { TrendChart } from '../components/TrendChart';
import { ScanTable } from '../components/ScanTable';
import { RiskIndicators } from '../components/RiskIndicators';
import { fetchDashboardSummary, fetchScanHistory } from '../lib/api';
import { Card, Flex, Grid, Text } from '@radix-ui/themes';

export default function DashboardPage() {
  const { data: summary } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchDashboardSummary,
  });
  const { data: scans = [] } = useQuery({
    queryKey: ['scan-history'],
    queryFn: fetchScanHistory,
  });

  const licenseDistribution = summary?.licenseDistribution ?? [];
  const trend = summary?.trend ?? [];

  return (
    <LayoutShell>
      <SummaryCards
        totalProjects={summary?.totalProjects ?? 0}
        totalViolations={summary?.totalViolations ?? 0}
        highRiskProjects={summary?.highRiskProjects ?? 0}
        pendingScans={summary?.pendingScans ?? 0}
      />
      <Grid columns={{ initial: '1', md: '3' }} gap="4" className="mb-6">
        <LicenseDistribution data={licenseDistribution} />
        <TrendChart data={trend} />
        <RiskIndicators
          highRiskProjects={summary?.highRiskProjects ?? 0}
          pendingScans={summary?.pendingScans ?? 0}
        />
      </Grid>
      <ScanTable scans={scans} />
      <Flex gap="4" className="mt-6" direction={{ initial: 'column', md: 'row' }}>
        <Card className="flex-1 border border-slate-800 bg-slate-900">
          <Text size="3" weight="medium" className="mb-3 block">
            Quick Actions
          </Text>
          <Flex direction="column" gap="3" className="text-sm text-slate-300">
            <Text as="a" href="/scans" className="text-sky-400 hover:underline">
              Launch a new scan
            </Text>
            <Text as="a" href="/policies" className="text-sky-400 hover:underline">
              Review policy templates
            </Text>
            <Text as="a" href="/auth/signin" className="text-sky-400 hover:underline">
              Configure alerts and notifications
            </Text>
          </Flex>
        </Card>
        <Card className="flex-1 border border-slate-800 bg-slate-900">
          <Text size="3" weight="medium" className="mb-3 block">
            Compliance Checklist
          </Text>
          <ul className="space-y-2 text-sm text-slate-300 list-disc list-inside">
            <li>Validate policy decisions against legal review.</li>
            <li>Ensure Redis queue is monitored for stuck jobs.</li>
            <li>Confirm CI pipelines upload latest compliance reports.</li>
            <li>Review high-risk projects weekly with engineering leads.</li>
          </ul>
        </Card>
      </Flex>
    </LayoutShell>
  );
}
