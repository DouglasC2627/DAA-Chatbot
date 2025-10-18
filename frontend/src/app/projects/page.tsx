import MainLayout from '@/components/layout/MainLayout';
import ProjectCreate from '@/components/projects/ProjectCreate';
import ProjectList from '@/components/projects/ProjectList';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

export default function ProjectsPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
            <p className="text-muted-foreground mt-2">
              Manage your RAG projects and organize your documents
            </p>
          </div>
          <ProjectCreate />
        </div>

        {/* Project List */}
        <ProjectList />
      </div>
    </MainLayout>
  );
}
