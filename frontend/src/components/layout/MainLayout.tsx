'use client';

import { ReactNode } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';
import Breadcrumb from './Breadcrumb';

interface MainLayoutProps {
  children: ReactNode;
  showBreadcrumb?: boolean;
}

export default function MainLayout({ children, showBreadcrumb = true }: MainLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 md:ml-64 overflow-y-auto">
          <div className="container max-w-7xl mx-auto p-4 md:p-6 lg:p-8">
            {showBreadcrumb && <Breadcrumb />}
            {children}
          </div>
        </main>
      </div>
      <Footer />
    </div>
  );
}
