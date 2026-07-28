"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Play, CheckCircle2, Clock, XCircle, Loader2 } from "lucide-react";
import { useStore } from "@/lib/store";
import { Header } from "@/components/header";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";

export default function WorkflowsPage() {
  const {
    workflows,
    workflowsLoading,
    fetchWorkflows,
    runs,
    triggerRun,
    error,
  } = useStore();

  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  const statusVariant = (status: string) => {
    switch (status) {
      case "SUCCESS": return "success";
      case "RUNNING":
      case "PENDING": return "info";
      case "PAUSED": return "warning";
      default: return "error";
    }
  };

  return (
    <div className="min-h-screen">
      <Header />

      <main className="pt-24 pb-16">
        <div className="container-custom">
          {/* Page header */}
          <div className="flex items-center gap-4 mb-8">
            <Link href="/" className="p-2 rounded-lg text-neutral-500 hover:text-white hover:bg-white/5 transition-colors">
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-white">
                Workflows
              </h1>
              <p className="text-sm text-neutral-500 mt-1">Manage and execute your agent workflows</p>
            </div>
          </div>

          {error && (
            <div className="mb-6 bg-red-500/10 border border-red-500/20 text-red-400 text-sm px-4 py-3 rounded-xl">
              {error}
            </div>
          )}

          {/* Workflow definitions */}
          <Card className="p-6 mb-6">
            <h3 className="text-sm font-semibold text-white mb-4">Registered Workflows</h3>
            {workflowsLoading ? (
              <div className="flex items-center justify-center py-8 text-neutral-500">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Loading workflows...
              </div>
            ) : workflows.length === 0 ? (
              <p className="text-sm text-neutral-600 text-center py-8">No workflows found. Create one via the API or CLI.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Nodes</TableHead>
                    <TableHead>Version</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {workflows.map((wf) => (
                    <TableRow key={wf.id}>
                      <TableCell className="font-mono text-xs text-neutral-500">{wf.id.slice(0, 8)}...</TableCell>
                      <TableCell className="font-medium text-neutral-200">{wf.name}</TableCell>
                      <TableCell className="text-neutral-400">{wf.definition?.nodes?.length ?? 0}</TableCell>
                      <TableCell className="text-neutral-400">v{wf.version}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => triggerRun(wf.id)}
                          className="gap-1.5"
                        >
                          <Play className="h-3 w-3" /> Run
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>

          {/* Run history */}
          <Card className="p-6">
            <h3 className="text-sm font-semibold text-white mb-4">Execution Runs</h3>
            {runs.length === 0 ? (
              <p className="text-sm text-neutral-600 text-center py-8">No runs yet. Trigger a workflow to see history.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Run ID</TableHead>
                    <TableHead>Workflow</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Version</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.map((run) => (
                    <TableRow key={run.run_id}>
                      <TableCell className="font-mono text-xs text-emerald-400">{run.run_id.slice(0, 8)}...</TableCell>
                      <TableCell className="font-mono text-xs text-neutral-500">{run.workflow_id.slice(0, 8)}...</TableCell>
                      <TableCell>
                        <Badge variant={statusVariant(run.status)}>
                          {run.status === "SUCCESS" && <CheckCircle2 className="h-3 w-3" />}
                          {(run.status === "RUNNING" || run.status === "PENDING") && <Clock className="h-3 w-3" />}
                          {run.status === "FAILED" && <XCircle className="h-3 w-3" />}
                          {run.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-neutral-400">v{run.version}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>
        </div>
      </main>
    </div>
  );
}
