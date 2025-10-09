// Copyright 2025 Ajay Pundhir
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

"use client";

import { useState, useEffect, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getScans, createScan, getPolicies, getScanProgress, api } from "@/lib/api";
import { ContentLayout } from "@/components/admin-panel/content-layout";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import {
  ScanSearch,
  Loader2,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Clock,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export default function ScansPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [repoUrl, setRepoUrl] = useState("");
  const [projectName, setProjectName] = useState("");
  const [selectedPolicy, setSelectedPolicy] = useState("");
  const [checkVulnerabilities, setCheckVulnerabilities] = useState(false);
  const [activeScanId, setActiveScanId] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const queryClient = useQueryClient();
  const router = useRouter();

  const { data: scans, isLoading, error } = useQuery({
    queryKey: ["scans"],
    queryFn: getScans,
    retry: 1,
    // Faster polling when there are running scans, slower when all complete
    refetchInterval: (data) => {
      const hasRunning = (Array.isArray(data) && data.some((scan: any) => scan.status.toLowerCase() === "running")) || activeScanId !== null;
      return hasRunning ? 3000 : 30000;
    },
  });

  const { data: policies, error: policiesError } = useQuery({
    queryKey: ["policies"],
    queryFn: getPolicies,
    retry: 1,
  });

  // Poll progress for active scan
  const { data: progress } = useQuery({
    queryKey: ["scan-progress", activeScanId],
    queryFn: () => getScanProgress(activeScanId!),
    enabled: !!activeScanId && !showSuccess,
    refetchInterval: (data) => {
      // Stop polling if scan is complete or failed
      const scanStatus = data?.status?.toLowerCase();
      if (scanStatus === "complete" || scanStatus === "failed") {
        return false;
      }
      return 1500; // Poll every 1.5 seconds
      return 1500; // Poll every 1.5 seconds
    },
    retry: false,
  });

  // Handle progress completion
  useEffect(() => {
    if (progress?.status === "complete" || progress?.status === "failed") {
      setShowSuccess(true);
      queryClient.invalidateQueries({ queryKey: ["scans"] });

      // Auto-close modal after showing success for 2 seconds
      const timer = setTimeout(() => {
        setIsDialogOpen(false);
        setActiveScanId(null);
        setShowSuccess(false);
        setRepoUrl("");
        setProjectName("");
        setSelectedPolicy("");
        setCheckVulnerabilities(false);

        // Navigate to scan details if successful
        if (progress.status === "complete") {
          router.push(`/scans/${activeScanId}`);
        }
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [progress?.status, activeScanId, queryClient, router]);

  const createScanMutation = useMutation({
    mutationFn: (data: { repoUrl: string; projectName: string; policy?: string; checkVulnerabilities?: boolean }) => {
      // Direct API call if lib/api wrapper doesn't support extra args yet
      return api.post("/scans", {
        repo_url: data.repoUrl,
        project_name: data.projectName,
        policy: data.policy,
        check_vulnerabilities: data.checkVulnerabilities
      }).then(res => res.data);
    },
    onSuccess: (data: any) => {
      // Clear submission state
      setIsSubmitting(false);

      const scanId = data.id || data.scan_id;

      // Optimistically add scan to table
      queryClient.setQueryData(["scans"], (old: any) => {
        const newScan = {
          id: scanId,
          project: data.project || projectName,
          status: "queued",
          violations: 0,
          warnings: 0,
          generatedAt: new Date().toISOString(),
          durationSeconds: 0,
        };
        return [newScan, ...(old || [])];
      });

      toast.success("Scan submitted successfully!");

      // Close dialog immediately
      setIsDialogOpen(false);
      setRepoUrl("");
      setProjectName("");
      setSelectedPolicy("");
      setCheckVulnerabilities(false);
      setActiveScanId(null);

      // Refresh scans list
      queryClient.invalidateQueries({ queryKey: ["scans"] });
    },
    onError: (error: any) => {
      // Clear submission state
      setIsSubmitting(false);

      console.error("Scan creation error:", error);

      // Handle different error formats
      let errorMsg = "Failed to create scan";

      if (error.response?.data) {
        const data = error.response.data;

        // Handle Pydantic validation errors (422)
        if (Array.isArray(data.detail)) {
          errorMsg = data.detail.map((err: any) => err.msg).join(", ");
        } else if (typeof data.detail === 'string') {
          errorMsg = data.detail;
        } else if (data.message) {
          errorMsg = data.message;
        }
      }

      toast.error(errorMsg);
    },
  });

  const handleCreateScan = () => {
    if (!repoUrl.trim()) {
      toast.error("Please enter a GitHub repository URL");
      return;
    }

    // Validate GitHub URL format
    const githubUrlPattern = /^https?:\/\/(www\.)?github\.com\/[\w-]+\/[\w.-]+/;
    if (!githubUrlPattern.test(repoUrl)) {
      toast.error("Please enter a valid GitHub repository URL");
      return;
    }

    // Extract project name from URL if not provided
    let finalProjectName = projectName.trim();
    if (!finalProjectName) {
      const match = repoUrl.match(/github\.com\/([\w-]+)\/([\w.-]+)/);
      if (match) {
        finalProjectName = match[2].replace(/\.git$/, "");
      }
    }

    // Set submitting state
    setIsSubmitting(true);

    // Note: Currently scans /workspace, GitHub cloning to be implemented in backend
    createScanMutation.mutate({
      repoUrl: repoUrl.trim(),
      projectName: finalProjectName,
      policy: selectedPolicy === "none" ? undefined : selectedPolicy,
      checkVulnerabilities: checkVulnerabilities,
    });
  };

  const getStatusBadge = (scan: any) => {
    const status = scan.status.toLowerCase();

    if (status === "running" || status === "queued") {
      return (
        <div className="flex flex-col gap-1 min-w-[140px]">
          <div className="flex items-center justify-between text-xs">
            <Badge variant="secondary" className="mr-2">
              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              {scan.current_stage ? scan.current_stage.replace(/_/g, " ") : status}
            </Badge>
            <span className="text-muted-foreground">{scan.progress_percent || 0}%</span>
          </div>
          <Progress value={scan.progress_percent || 0} className="h-1.5" />
        </div>
      );
    }

    switch (status) {
      case "completed":
        return (
          <Badge variant="default" className="bg-green-500 hover:bg-green-600">
            <CheckCircle2 className="mr-1 h-3 w-3" />
            Completed
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="destructive">
            <XCircle className="mr-1 h-3 w-3" />
            Failed
          </Badge>
        );
      default:
        return (
          <Badge variant="outline">
            <Clock className="mr-1 h-3 w-3" />
            {scan.status}
          </Badge>
        );
    }
  };

  return (
    <ContentLayout title="Scans">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Scan History</h2>
            <p className="text-muted-foreground mt-2">
              View and manage all compliance scans across your projects
            </p>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <ScanSearch className="mr-2 h-4 w-4" />
                New Scan
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Scan GitHub Repository</DialogTitle>
                <DialogDescription>
                  Enter a GitHub repository URL to clone and scan for license compliance issues.
                </DialogDescription>
              </DialogHeader>

              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="repoUrl">GitHub Repository URL *</Label>
                  <Input
                    id="repoUrl"
                    placeholder="https://github.com/username/repository"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    disabled={createScanMutation.isPending}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="projectName">Project Name (Optional)</Label>
                  <Input
                    id="projectName"
                    placeholder="my-project"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    disabled={createScanMutation.isPending}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="policy">Compliance Policy (Optional)</Label>
                  <Select
                    value={selectedPolicy}
                    onValueChange={setSelectedPolicy}
                    disabled={createScanMutation.isPending}
                  >
                    <SelectTrigger id="policy">
                      <SelectValue placeholder="Select a policy" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">No Policy</SelectItem>
                      {policies?.map((policy: any) => (
                        <SelectItem key={policy.name} value={policy.name}>
                          {policy.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="checkVulnerabilities"
                    checked={checkVulnerabilities}
                    onCheckedChange={(checked) => setCheckVulnerabilities(checked as boolean)}
                    disabled={createScanMutation.isPending}
                  />
                  <Label htmlFor="checkVulnerabilities" className="font-normal cursor-pointer">
                    Check for Security Vulnerabilities (OSV)
                  </Label>
                </div>
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsDialogOpen(false)}
                  disabled={createScanMutation.isPending}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateScan}
                  disabled={createScanMutation.isPending}
                >
                  {createScanMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <ScanSearch className="mr-2 h-4 w-4" />
                      Create Scan
                    </>
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Recent Scans</CardTitle>
            <CardDescription>
              All automated and manual scans with their compliance status
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center py-12 space-y-3">
                <AlertCircle className="h-12 w-12 text-destructive" />
                <p className="text-sm text-muted-foreground">
                  Failed to load scans. Make sure the backend API is running.
                </p>
              </div>
            ) : !scans || scans.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 space-y-3">
                <ScanSearch className="h-12 w-12 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  No scans found. Create your first scan to get started.
                </p>
                <Button onClick={() => setIsDialogOpen(true)}>
                  <ScanSearch className="mr-2 h-4 w-4" />
                  Create First Scan
                </Button>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Scan ID</TableHead>
                    <TableHead>Project</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Violations</TableHead>
                    <TableHead>Warnings</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {scans.map((scan: any) => (
                    <TableRow key={scan.id}>
                      <TableCell className="font-mono text-xs">
                        {scan.id.substring(0, 8)}
                      </TableCell>
                      <TableCell className="font-medium">
                        {scan.project || "Unknown"}
                      </TableCell>
                      <TableCell>{getStatusBadge(scan)}</TableCell>
                      <TableCell>
                        <span className="text-destructive font-medium">
                          {scan.violations || 0}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-yellow-500 font-medium">
                          {scan.warnings || 0}
                        </span>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {new Date(scan.generatedAt).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" asChild>
                          <Link href={`/scans/${scan.id}`}>View Details</Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </ContentLayout>
  );
}
