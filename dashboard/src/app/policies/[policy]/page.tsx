'use client';

import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { LayoutShell } from '../../../components/LayoutShell';
import { fetchPolicy } from '../../../lib/api';
import { Badge, Card, Flex, Grid, Heading, Separator, Text } from '@radix-ui/themes';
import Link from 'next/link';
import { LegalNotice } from '../../../components/LegalNotice';

type PolicyPageProps = {
  params: {
    policy: string;
  };
};

export default function PolicyDetailPage({ params }: PolicyPageProps) {
  const { data: policy, isLoading } = useQuery({
    queryKey: ['policy-detail', params.policy],
    queryFn: () => fetchPolicy(params.policy),
  });

  const title = useMemo(() => params.policy.replace(/-/g, ' '), [params.policy]);

  return (
    <LayoutShell>
      <Flex direction="column" gap="3" className="mb-6">
        <Flex align="center" justify="between">
          <div>
            <Heading size="6" className="capitalize">
              {title}
            </Heading>
            <Text size="2" color="gray">
              Policy governance detail and context-specific guidance.
            </Text>
          </div>
          <Text asChild size="2">
            <Link href="/policies" className="text-sky-400 hover:underline">
              ← Back to policies
            </Link>
          </Text>
        </Flex>
        {policy?.disclaimer ? <LegalNotice message={policy.disclaimer} /> : null}
      </Flex>

      {isLoading && <Text color="gray">Loading policy…</Text>}

      {!isLoading && !policy && <Text color="red">Policy template not found.</Text>}

      {policy ? (
        <Flex direction="column" gap="6">
          <Card className="border border-slate-800 bg-slate-900">
            <Flex direction="column" gap="2">
              <Text size="3" weight="medium">
                {policy.description}
              </Text>
              <Flex align="center" gap="3">
                <Badge color={policy.status === 'active' ? 'green' : 'amber'}>{policy.status}</Badge>
                <Text size="1" color="gray">
                  Last updated: {policy.lastUpdated}
                </Text>
              </Flex>
            </Flex>
          </Card>

          <Flex direction="column" gap="4">
            <Heading size="4">Contexts</Heading>
            <Grid columns={{ initial: '1', md: '2' }} gap="4">
              {policy.contexts.map((context) => (
                <Card key={context.name} className="border border-slate-800 bg-slate-900">
                  <Flex direction="column" gap="3">
                    <Heading size="3" className="capitalize">
                      {context.name}
                    </Heading>
                    <Flex gap="2" wrap="wrap">
                      <Badge color="blue">Dual-license: {context.dualLicensePreference}</Badge>
                    </Flex>
                    <Separator className="border-slate-800" />
                    <ContextList title="Allow" items={context.allow} badgeColor="green" />
                    <ContextList title="Review" items={context.review} badgeColor="amber" />
                    <ContextList title="Deny" items={context.deny} badgeColor="red" />
                  </Flex>
                </Card>
              ))}
            </Grid>
          </Flex>
        </Flex>
      ) : null}
    </LayoutShell>
  );
}

type ContextListProps = {
  title: string;
  items: string[];
  badgeColor: 'green' | 'amber' | 'red';
};

function ContextList({ title, items, badgeColor }: ContextListProps) {
  return (
    <Flex direction="column" gap="2">
      <Text size="2" weight="medium">
        {title}
      </Text>
      <Flex gap="2" wrap="wrap">
        {items.length ? (
          items.map((item) => (
            <Badge key={item} color={badgeColor} variant="soft">
              {item}
            </Badge>
          ))
        ) : (
          <Text size="1" color="gray">
            None specified
          </Text>
        )}
      </Flex>
    </Flex>
  );
}
