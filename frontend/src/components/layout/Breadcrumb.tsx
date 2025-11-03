'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRight, Home } from 'lucide-react';
import { useShallow } from 'zustand/react/shallow';
import { useProjectStore } from '@/stores/projectStore';
import { Fragment } from 'react';

interface BreadcrumbItem {
  label: string;
  href: string;
  icon?: React.ReactNode;
}

export default function Breadcrumb() {
  const pathname = usePathname();
  const currentProject = useProjectStore(
    useShallow((state) => state.projects.find((project) => project.id === state.currentProjectId))
  );

  // Generate breadcrumb items based on current path
  const getBreadcrumbs = (): BreadcrumbItem[] => {
    const paths = pathname.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [
      { label: 'Home', href: '/', icon: <Home className="h-3 w-3" /> },
    ];

    // Build breadcrumbs from path segments
    let currentPath = '';
    paths.forEach((segment, index) => {
      currentPath += `/${segment}`;

      // Skip dynamic route segments like [id]
      if (segment.startsWith('[')) return;

      const label = segment.charAt(0).toUpperCase() + segment.slice(1);

      // Special handling for known routes
      if (segment === 'projects' && currentProject && index === paths.length - 1) {
        breadcrumbs.push({ label: 'Projects', href: '/projects' });
      } else if (segment === 'documents') {
        breadcrumbs.push({ label: 'Documents', href: '/documents' });
      } else if (segment === 'chats') {
        breadcrumbs.push({ label: 'Chats', href: '/chats' });
      } else if (segment === 'settings') {
        breadcrumbs.push({ label: 'Settings', href: '/settings' });
      } else if (segment === 'chat' && currentProject) {
        breadcrumbs.push({ label: 'Chat', href: `/chat/${currentProject.id}` });
      } else {
        // For dynamic segments, try to get more meaningful labels
        if (currentProject && paths[index - 1] === 'projects') {
          breadcrumbs.push({ label: currentProject.name, href: currentPath });
        } else if (!segment.match(/^[0-9a-f-]{36}$/i)) {
          // Skip UUIDs and similar IDs
          breadcrumbs.push({ label, href: currentPath });
        }
      }
    });

    return breadcrumbs;
  };

  const breadcrumbs = getBreadcrumbs();

  // Don't show breadcrumbs on home page
  if (pathname === '/') {
    return null;
  }

  return (
    <nav className="flex items-center space-x-1 text-sm text-muted-foreground mb-4">
      {breadcrumbs.map((item, index) => {
        const isLast = index === breadcrumbs.length - 1;

        return (
          <Fragment key={item.href}>
            {index > 0 && <ChevronRight className="h-4 w-4 flex-shrink-0" />}
            {isLast ? (
              <span className="flex items-center gap-1 font-medium text-foreground">
                {item.icon}
                {item.label}
              </span>
            ) : (
              <Link
                href={item.href}
                className="flex items-center gap-1 hover:text-foreground transition-colors"
              >
                {item.icon}
                {item.label}
              </Link>
            )}
          </Fragment>
        );
      })}
    </nav>
  );
}
