'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BellIcon, DashboardIcon, GearIcon, LockClosedIcon, TableIcon } from '@radix-ui/react-icons';
import { Avatar, Box, Button, Flex, Heading, IconButton, Separator, Text } from '@radix-ui/themes';
import { ReactNode } from 'react';
import { useAuth } from '../lib/auth';
import { LegalNotice } from './LegalNotice';

const navItems = [
  { href: '/', label: 'Dashboard', icon: <DashboardIcon /> },
  { href: '/scans', label: 'Scans', icon: <TableIcon /> },
  { href: '/policies', label: 'Policies', icon: <GearIcon /> },
];

export function LayoutShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user, signOut } = useAuth();

  return (
    <Flex direction="column" minHeight="100vh">
      <Flex as="header" px="4" py="3" justify="between" align="center" className="bg-slate-900 border-b border-slate-800">
        <Flex align="center" gap="3">
          <Link href="/" className="text-xl font-semibold text-sky-400">
            LCC Dashboard
          </Link>
          <Separator orientation="vertical" className="h-6" />
          <Flex gap="2">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors hover:bg-slate-800 ${pathname === item.href ? 'bg-slate-800 text-sky-400' : 'text-slate-200'}`}
              >
                {item.icon}
                {item.label}
              </Link>
            ))}
          </Flex>
        </Flex>
        <Flex align="center" gap="3">
          <IconButton variant="soft" color="gray" radius="full">
            <BellIcon />
          </IconButton>
          <Flex align="center" gap="2">
            <Avatar fallback={user?.name?.[0].toUpperCase() ?? 'U'} size="2" />
            <Flex direction="column">
              <Text size="2" weight="medium">
                {user?.name ?? 'Guest'}
              </Text>
              <Text size="1" color="gray">
                {user?.email ?? 'Not signed in'}
              </Text>
            </Flex>
          </Flex>
          {user ? (
            <Button variant="soft" color="gray" onClick={() => signOut()}>
              Sign out
            </Button>
          ) : (
            <Button variant="solid" color="blue" asChild>
              <Link href="/auth/signin">Sign in</Link>
            </Button>
          )}
        </Flex>
      </Flex>
      <Flex as="main" grow="1" className="bg-slate-950" px="6" py="6">
        <Box className="w-full max-w-6xl mx-auto">
          <LegalNotice />
          {children}
        </Box>
      </Flex>
      <Flex as="footer" justify="between" align="center" px="6" py="4" className="border-t border-slate-900 bg-slate-950 text-slate-400 text-sm">
        <Text>&copy; {new Date().getFullYear()} License Compliance Checker</Text>
        <Flex gap="3" align="center">
          <LockClosedIcon />
          <Text>Secure &amp; auditable</Text>
        </Flex>
      </Flex>
    </Flex>
  );
}
