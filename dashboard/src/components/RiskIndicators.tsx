'use client';

import { Card, Flex, Text } from '@radix-ui/themes';
import { ShieldExclamationIcon } from '@radix-ui/react-icons';

interface RiskIndicatorsProps {
  highRiskProjects: number;
  pendingScans: number;
}

export function RiskIndicators({ highRiskProjects, pendingScans }: RiskIndicatorsProps) {
  const indicators = [
    {
      label: 'High-risk Projects',
      description: 'Projects with active policy violations that need attention.',
      value: highRiskProjects,
    },
    {
      label: 'Pending Scans',
      description: 'Queued or running scans. Monitor capacity and SLAs.',
      value: pendingScans,
    },
  ];
  return (
    <Card className="border border-slate-800 bg-slate-900">
      <Flex direction="column" gap="4">
        <Text size="3" weight="medium">
          Risk Indicators
        </Text>
        {indicators.map((indicator) => (
          <Flex key={indicator.label} align="center" gap="3" className="p-3 rounded-md bg-slate-950 border border-slate-800">
            <ShieldExclamationIcon width={24} height={24} className="text-amber-400" />
            <Flex direction="column">
              <Text weight="medium">{indicator.label}</Text>
              <Text color="gray" size="1">
                {indicator.description}
              </Text>
            </Flex>
            <Text weight="bold" className="ml-auto text-amber-300">
              {indicator.value}
            </Text>
          </Flex>
        ))}
      </Flex>
    </Card>
  );
}
