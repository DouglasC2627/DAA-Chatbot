import Link from 'next/link';
import { BarChart3 } from 'lucide-react';
import MainLayout from '@/components/layout/MainLayout';
import DocumentUpload from '@/components/documents/DocumentUpload';
import DocumentList from '@/components/documents/DocumentList';
import { Button } from '@/components/ui/button';

export default function DocumentsPage() {
  return (
    <MainLayout>
      <div className="space-y-8">
        {/* Header Section */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
            <p className="text-muted-foreground mt-2">
              Upload and manage documents for RAG-powered conversations
            </p>
          </div>
          <Link href="/analytics">
            <Button variant="outline" className="gap-2">
              <BarChart3 className="h-4 w-4" />
              View Analytics
            </Button>
          </Link>
        </div>

        {/* Upload Section */}
        <DocumentUpload />

        {/* Documents List Section */}
        <div>
          <h2 className="text-2xl font-semibold mb-4">Your Documents</h2>
          <DocumentList />
        </div>
      </div>
    </MainLayout>
  );
}
