'use client';

import { useQuery } from '@tanstack/react-query';
import { LayoutShell } from '../../components/LayoutShell';
import { Card, Flex, Grid, Text, Button } from '@radix-ui/themes';
import { fetchPolicies } from '../../lib/api';
import Link from 'next/link';
import { LegalNotice } from '../../components/LegalNotice';

export default function PoliciesPage() {
  const { data: policies = [] } = useQuery({
    queryKey: ['policies'],
    queryFn: fetchPolicies,
  });

  return (
    <LayoutShell>
      <Flex justify="between" align="center" className="mb-6">
        <div>
          <Text size="4" weight="medium">
            Policies
          </Text>
          <Text size="2" color="gray">
            Manage policy templates and active compliance rules.
          </Text>
        </div>
        <Button asChild>
          <Link href="https://github.com/apundhir/licence-compliance-checker/tree/main/policies" target="_blank">
            View repository templates
          </Link>
        </Button>
      </Flex>
      <Grid columns={{ initial: '1', md: '2' }} gap="4">
        {policies.map((policy) => (
          <Card key={policy.name} className="border border-slate-800 bg-slate-900">
            <Flex direction="column" gap="2">
              <Text size="3" weight="medium">
                {policy.name}
              </Text>
              <Text size="2" color="gray">
                {policy.description}
              </Text>
              <Text size="1" color="gray">
                Last updated: {policy.lastUpdated}
              </Text>
              {policy.disclaimer ? <LegalNotice message={policy.disclaimer} /> : null}
              <Flex gap="2" className="mt-3">
                <Button variant="soft" asChild>
                  <Link href={`/policies/${policy.name}`}>View details</Link>
                </Button>
                <Button variant="outline" color="gray" asChild>
                  <a href={`/api/policies/${policy.name}?download=1`}>Download</a>
                </Button>
              </Flex>
            </Flex>
          </Card>
        ))}
      </Grid>
      <Card className="mt-6 border border-slate-800 bg-slate-900">
        <Text size="3" weight="medium" className="mb-3 block">
          Template Guidance
        </Text>
        <ul className="space-y-2 text-sm text-slate-300 list-disc list-inside">
          <li>Use the CLI (`lcc policy import/export`) to synchronise policies with the server.</li>
          <li>Reference `policy/templates` for curated starting points.</li>
          <li>Document overrides and approvals for audit readiness.</li>
        </ul>
      </Card>
    </LayoutShell>
  );
}
