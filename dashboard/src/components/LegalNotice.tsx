'use client';

import { Callout, Text } from '@radix-ui/themes';

const DEFAULT_MESSAGE =
  'LCC surfaces automated policy guidance only. Always consult qualified legal counsel before acting on licensing decisions.';

type LegalNoticeProps = {
  message?: string;
};

export function LegalNotice({ message = DEFAULT_MESSAGE }: LegalNoticeProps) {
  return (
    <Callout.Root color="amber" role="status" className="mb-4 border border-amber-400/40 bg-amber-100/10">
      <Callout.Icon>
        <span aria-hidden="true">⚖️</span>
      </Callout.Icon>
      <Callout.Text>
        <Text size="2" className="text-amber-100">
          {message}
        </Text>
      </Callout.Text>
    </Callout.Root>
  );
}
