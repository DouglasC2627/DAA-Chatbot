'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { Moon, Sun, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTheme } from '@/components/theme-provider';
import MobileNav from './MobileNav';
import ChatSettingsPanel from '@/components/chat/ChatSettingsPanel';
import { cn } from '@/lib/utils';

export default function Header() {
  const { theme, setTheme } = useTheme();
  const pathname = usePathname();
  const [settingsOpen, setSettingsOpen] = useState(false);

  const isActive = (path: string) => pathname === path;

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 md:h-16 items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-4 md:gap-6">
          <Link href="/" className="flex items-center space-x-2">
            <Image
              src="/favicon/favicon-32x32.png"
              alt="DAA Chatbot Logo"
              width={24}
              height={24}
              className="h-5 w-5 md:h-6 md:w-6"
            />
            <span className="font-bold text-lg md:text-xl">DAA Chatbot</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="/projects"
              className={cn(
                'text-sm font-medium transition-colors hover:text-primary',
                isActive('/projects') ? 'text-primary' : 'text-muted-foreground'
              )}
            >
              Projects
            </Link>
            <Link
              href="/documents"
              className={cn(
                'text-sm font-medium transition-colors hover:text-primary',
                isActive('/documents') ? 'text-primary' : 'text-muted-foreground'
              )}
            >
              Documents
            </Link>
            <Link
              href="/chats"
              className={cn(
                'text-sm font-medium transition-colors hover:text-primary',
                isActive('/chats') ? 'text-primary' : 'text-muted-foreground'
              )}
            >
              Chats
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-1 md:gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSettingsOpen(true)}
            aria-label="Open settings"
          >
            <Settings className="h-4 w-4 md:h-5 md:w-5" />
            <span className="sr-only">Settings</span>
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            aria-label="Toggle theme"
          >
            <Sun className="h-4 w-4 md:h-5 md:w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 md:h-5 md:w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Toggle theme</span>
          </Button>

          <MobileNav />
        </div>
      </div>

      {/* Settings Panel */}
      <ChatSettingsPanel open={settingsOpen} onOpenChange={setSettingsOpen} />
    </header>
  );
}
