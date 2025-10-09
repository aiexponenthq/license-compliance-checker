'use client';

import { Card, Flex, Grid, Text } from '@radix-ui/themes';

interface SummaryCardsProps {
  totalProjects: number;
  totalViolations: number;
  highRiskProjects: number;
  pendingScans: number;
}

const toneClass = {
  projects: 'text-sky-400',
  violations: 'text-red-400',
  highRisk: 'text-amber-400',
  pending: 'text-purple-400',
} as const;

export function SummaryCards({ totalProjects, totalViolations, highRiskProjects, pendingScans }: SummaryCardsProps) {
  const items = [
    { label: 'Projects', value: totalProjects, className: toneClass.projects },
    { label: 'Violations', value: totalViolations, className: toneClass.violations },
    { label: 'High-risk Projects', value: highRiskProjects, className: toneClass.highRisk },
    { label: 'Scans in Queue', value: pendingScans, className: toneClass.pending },
  ];

  return (
    <Grid columns={{ initial: '2', md: '4' }} gap="4" className="mb-6">
      {items.map((item) => (
        <Card key={item.label} className="border border-slate-800 bg-slate-900">
          <Flex direction="column" gap="2">
            <Text size="1" color="gray">
              {item.label}
            </Text>
            <Text size="6" weight="bold" className={item.className}>
              {item.value}
            </Text>
          </Flex>
        </Card>
      ))}
    </Grid>
  );
}
