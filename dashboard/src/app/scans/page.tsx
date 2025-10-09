'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { LayoutShell } from '../../components/LayoutShell';
import { createScan, fetchScanHistory } from '../../lib/api';
import { ScanTable } from '../../components/ScanTable';
import { Box, Button, Card, Flex, Select, TextField, Text } from '@radix-ui/themes';
import { useState } from 'react';

export default function ScansPage() {
  const queryClient = useQueryClient();
  const { data: scans = [], isFetching } = useQuery({
    queryKey: ['scan-history'],
    queryFn: fetchScanHistory,
  });
  const [project, setProject] = useState('');
  const [policy, setPolicy] = useState('permissive');

  const createScanMutation = useMutation({
    mutationFn: createScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scan-history'] });
      setProject('');
    },
  });

  return (
    <LayoutShell>
      <Flex direction={{ initial: 'column', md: 'row' }} gap="4" className="mb-6">
        <Card className="flex-1 border border-slate-800 bg-slate-900">
          <Text size="3" weight="medium" className="mb-3 block">
            Launch New Scan
          </Text>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              createScanMutation.mutate({ project, policy });
            }}
          >
            <Flex direction="column" gap="3">
              <label className="text-sm text-slate-300" htmlFor="project">
                Project path or repository
              </label>
              <TextField.Root
                id="project"
                placeholder="e.g. services/payments"
                value={project}
                onChange={(event) => setProject(event.target.value)}
                required
              />
              <label className="text-sm text-slate-300" htmlFor="policy">
                Policy
              </label>
              <Select.Root value={policy} onValueChange={setPolicy}>
                <Select.Trigger id="policy" className="bg-slate-950" />
                <Select.Content>
                  <Select.Item value="permissive">Permissive</Select.Item>
                  <Select.Item value="mobile-app">Mobile App</Select.Item>
                  <Select.Item value="enterprise-saas">Enterprise SaaS</Select.Item>
                  <Select.Item value="ai-research">AI Research</Select.Item>
                </Select.Content>
              </Select.Root>
              <Button type="submit" disabled={createScanMutation.isPending}>
                {createScanMutation.isPending ? 'Submitting…' : 'Submit scan'}
              </Button>
              {createScanMutation.isSuccess && (
                <Text size="1" color="green">
                  Scan request submitted.
                </Text>
              )}
            </Flex>
          </form>
        </Card>
        <Card className="flex-1 border border-slate-800 bg-slate-900">
          <Text size="3" weight="medium" className="mb-3 block">
            Queue Health
          </Text>
          <Flex direction="column" gap="3" className="text-sm text-slate-300">
            <Text>Current queue length: 3</Text>
            <Text>Last worker heartbeat: 3 min ago</Text>
            <Text>Average job duration: 2m 15s</Text>
            <Text>Recommendations: scale workers when pending scans &gt; 5.</Text>
          </Flex>
        </Card>
      </Flex>
      <Box className="mb-3 flex items-center justify-between">
        <Text size="4" weight="medium">
          Scan History
        </Text>
        {isFetching && <Text color="gray">Refreshing…</Text>}
      </Box>
      <ScanTable scans={scans} />
    </LayoutShell>
  );
}
