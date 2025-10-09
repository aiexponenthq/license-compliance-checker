'use client';

import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';
import { LayoutShell } from '../../../components/LayoutShell';
import { useAuth } from '../../../lib/auth';
import { Button, Card, Flex, Text, TextField } from '@radix-ui/themes';

export default function SignInPage() {
  const { signIn } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await signIn(email, password);
    router.push('/');
  }

  return (
    <LayoutShell>
      <Flex justify="center" align="center" className="py-10">
        <Card className="w-full max-w-md border border-slate-800 bg-slate-900">
          <Text size="4" weight="medium" className="mb-4 block text-center">
            Sign in
          </Text>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Text size="1" color="gray" as="label" htmlFor="email">
                Email address
              </Text>
              <TextField.Root
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>
            <div>
              <Text size="1" color="gray" as="label" htmlFor="password">
                Password
              </Text>
              <TextField.Root
                id="password"
                type="password"
                placeholder="••••••"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full">
              Continue
            </Button>
          </form>
          <Flex justify="between" className="mt-4 text-sm">
            <a className="text-sky-400 hover:underline" href="#">
              Forgot password?
            </a>
            <a className="text-sky-400 hover:underline" href="#">
              Request access
            </a>
          </Flex>
        </Card>
      </Flex>
    </LayoutShell>
  );
}
