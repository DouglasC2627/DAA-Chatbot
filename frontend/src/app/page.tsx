import MainLayout from '@/components/layout/MainLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Link from 'next/link';
import {
  LaptopMinimalCheck,
  FileText,
  Zap,
  Folder,
  ChevronsLeftRightEllipsis,
  Slack,
} from 'lucide-react';

export default function Home() {
  return (
    <MainLayout>
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Hero Section */}
        <section className="text-center space-y-4 py-12">
          <h1 className="text-4xl font-bold tracking-tight lg:text-5xl"> Welcome to DAA Chatbot</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Your fully-local, privacy-focused RAG chatbot powered by Ollama. Chat with your
            documents securely on your machine.
          </p>
          <div className="flex justify-center pt-4">
            <Link href="/projects">
              <Button size="lg">
                <Folder className="mr-2 h-5 w-5" />
                Create Project
              </Button>
            </Link>
          </div>
        </section>

        {/* Features Grid */}
        <section className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <LaptopMinimalCheck className="h-8 w-8 mb-2 text-primary" />
              <CardTitle>Fully Local</CardTitle>
              <CardDescription>
                All processing happens on your machine. No data leaves your computer.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Powered by Ollama with models like Llama 3.2 and Mistral running locally.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <FileText className="h-8 w-8 mb-2 text-primary" />
              <CardTitle>Multi-Format Support</CardTitle>
              <CardDescription>
                Upload PDF, DOCX, TXT, CSV, XLSX and more document formats.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Advanced document processing with intelligent chunking and embeddings.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Zap className="h-8 w-8 mb-2 text-primary" />
              <CardTitle>Smart RAG Pipeline</CardTitle>
              <CardDescription>
                Retrieval-Augmented Generation for accurate, context-aware responses.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                ChromaDB vector store with source attribution and semantic search.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Folder className="h-8 w-8 mb-2 text-primary" />
              <CardTitle>Project Isolation</CardTitle>
              <CardDescription>
                Organize documents into separate projects with isolated contexts.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Keep your work organized with project-based document management.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <ChevronsLeftRightEllipsis className="h-8 w-8 mb-2 text-primary" />
              <CardTitle>Real-time Streaming</CardTitle>
              <CardDescription>
                Get responses as they're generated with WebSocket streaming.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Experience smooth, real-time interaction with your chatbot.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Slack className="h-8 w-8 mb-2 text-primary" />
              <CardTitle>Modern UI</CardTitle>
              <CardDescription>
                Beautiful, responsive interface built with Next.js and shadcn/ui.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Dark mode support and smooth animations for a delightful experience.
              </p>
            </CardContent>
          </Card>
        </section>

        {/* Getting Started */}
        <section className="bg-muted rounded-lg p-8">
          <h2 className="text-2xl font-bold mb-4">Getting Started</h2>
          <ol className="space-y-3 text-muted-foreground">
            <li className="flex gap-3">
              <span className="font-bold text-foreground">1.</span>
              <span>Create a new project or select an existing one</span>
            </li>
            <li className="flex gap-3">
              <span className="font-bold text-foreground">2.</span>
              <span>Upload your documents (PDF, DOCX, TXT, CSV, etc.)</span>
            </li>
            <li className="flex gap-3">
              <span className="font-bold text-foreground">3.</span>
              <span>Wait for documents to be processed and indexed</span>
            </li>
            <li className="flex gap-3">
              <span className="font-bold text-foreground">4.</span>
              <span>Start chatting with your documents!</span>
            </li>
          </ol>
        </section>
      </div>
    </MainLayout>
  );
}
