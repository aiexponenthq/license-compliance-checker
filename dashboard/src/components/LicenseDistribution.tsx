'use client';

import { Card, Flex, Text } from '@radix-ui/themes';

interface LicenseDistributionProps {
  data: { license: string; count: number }[];
}

export function LicenseDistribution({ data }: LicenseDistributionProps) {
  const total = data.reduce((sum, entry) => sum + entry.count, 0);
  return (
    <Card className="border border-slate-800 bg-slate-900">
      <Text size="3" weight="medium" className="mb-4 block">
        License Distribution
      </Text>
      <Flex direction="column" gap="3">
        {data.map((entry) => {
          const percentage = total === 0 ? 0 : Math.round((entry.count / total) * 100);
          return (
            <Flex key={entry.license} direction="column" gap="2">
              <Flex justify="between" align="center">
                <Text>{entry.license}</Text>
                <Text color="gray">{percentage}%</Text>
              </Flex>
              <div className="h-2 w-full overflow-hidden rounded bg-slate-800">
                <div
                  className="h-full rounded bg-gradient-to-r from-sky-500 to-blue-400"
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </Flex>
          );
        })}
      </Flex>
    </Card>
  );
}
