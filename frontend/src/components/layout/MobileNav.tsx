'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Folder, FileText, MessageSquare, Settings, Plus, Home, Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import ProjectSelector from './ProjectSelector';

const navigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Projects', href: '/projects', icon: Folder },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'Chats', href: '/chats', icon: MessageSquare },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-64">
        <SheetHeader>
          <SheetTitle className="text-left">DAA Chatbot</SheetTitle>
        </SheetHeader>
        <div className="flex h-full flex-col gap-4 py-4">
          {/* Project Selector */}
          <div className="space-y-2">
            <ProjectSelector />
            <Button className="w-full" size="sm">
              <Plus className="mr-2 h-4 w-4" />
              New Project
            </Button>
          </div>

          {/* Navigation Menu */}
          <nav className="flex flex-1 flex-col gap-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Footer Info */}
          <div className="border-t pt-4">
            <div className="text-xs text-muted-foreground">
              <p className="font-medium">DAA Chatbot</p>
              <p>Version 1.0.0</p>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
