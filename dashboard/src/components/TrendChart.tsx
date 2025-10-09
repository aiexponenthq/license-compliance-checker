'use client';

import { Card, Flex, Text } from '@radix-ui/themes';

interface TrendChartProps {
  data: { month: string; violations: number }[];
}

export function TrendChart({ data }: TrendChartProps) {
  const max = Math.max(...data.map((item) => item.violations), 1);
  return (
    <Card className="border border-slate-800 bg-slate-900 h-full">
      <Text size="3" weight="medium" className="mb-4 block">
        Violation Trend (last 6 months)
      </Text>
      <Flex align="end" gap="4" className="h-48">
        {data.map((item) => (
          <Flex key={item.month} direction="column" align="center" gap="2" className="w-10">
            <div
              className="w-full rounded-t bg-gradient-to-t from-red-500 to-amber-400"
              style={{ height: `${(item.violations / max) * 100}%` }}
            />
            <Text size="1" color="gray">
              {item.month}
            </Text>
          </Flex>
        ))}
      </Flex>
    </Card>
  );
}
