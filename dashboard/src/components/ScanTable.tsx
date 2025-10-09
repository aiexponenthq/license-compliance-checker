'use client';

import { Badge, Card, Flex, Table, Text } from '@radix-ui/themes';
import { ScanSummary } from '../lib/api';

const statusMap: Record<ScanSummary['status'], { label: string; color: 'jade' | 'amber' | 'red' | 'sky' }> = {
  pass: { label: 'Pass', color: 'jade' },
  warning: { label: 'Warning', color: 'amber' },
  violation: { label: 'Violation', color: 'red' },
  running: { label: 'Running', color: 'sky' },
};

interface ScanTableProps {
  scans: ScanSummary[];
}

export function ScanTable({ scans }: ScanTableProps) {
  return (
    <Card className="border border-slate-800 bg-slate-900">
      <Flex justify="between" align="center" className="mb-4">
        <Text size="3" weight="medium">
          Recent Scans
        </Text>
        <Text size="1" color="gray">
          Showing last {scans.length} scans
        </Text>
      </Flex>
      <Table.Root variant="surface">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeaderCell>Project</Table.ColumnHeaderCell>
            <Table.ColumnHeaderCell>Status</Table.ColumnHeaderCell>
            <Table.ColumnHeaderCell>Violations</Table.ColumnHeaderCell>
            <Table.ColumnHeaderCell>Generated</Table.ColumnHeaderCell>
            <Table.ColumnHeaderCell>Report</Table.ColumnHeaderCell>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {scans.map((scan) => {
            const status = statusMap[scan.status];
            return (
              <Table.Row key={scan.id}>
                <Table.Cell>{scan.project}</Table.Cell>
                <Table.Cell>
                  <Badge color={status.color}>{status.label}</Badge>
                </Table.Cell>
                <Table.Cell>{scan.violations}</Table.Cell>
                <Table.Cell>{new Date(scan.generatedAt).toLocaleString()}</Table.Cell>
                <Table.Cell>
                  {scan.reportUrl ? (
                    <a href={scan.reportUrl} className="text-sky-400 hover:underline">
                      Download
                    </a>
                  ) : (
                    <Text color="gray">Pending</Text>
                  )}
                </Table.Cell>
              </Table.Row>
            );
          })}
        </Table.Body>
      </Table.Root>
    </Card>
  );
}
