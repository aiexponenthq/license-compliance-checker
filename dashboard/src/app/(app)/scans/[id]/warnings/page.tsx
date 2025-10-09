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

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { ContentLayout } from "@/components/admin-panel/content-layout";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import {
  Loader2,
  AlertCircle,
  ArrowLeft,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Search,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";

interface WarningDetail {
  component_name: string;
  component_version: string | null;
  license: string;
  warning_type: string;
  severity: string;
  message: string;
  explanation: string;
  recommendation: string;
  details: Record<string, any>;
  learn_more_url: string | null;
}

interface WarningsSummary {
  total_warnings: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
  warnings: WarningDetail[];
}

async function getScanWarnings(id: string): Promise<WarningsSummary> {
  const response = await api.get(`/scans/${id}/warnings`);
  return response.data;
}

function getSeverityBadge(severity: string) {
  switch (severity.toLowerCase()) {
    case "high":
      return (
        <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
          <AlertTriangle className="mr-1 h-3 w-3" />
          High
        </Badge>
      );
    case "medium":
      return (
        <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
          <AlertTriangle className="mr-1 h-3 w-3" />
          Medium
        </Badge>
      );
    case "low":
      return (
        <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
          <AlertCircle className="mr-1 h-3 w-3" />
          Low
        </Badge>
      );
    default:
      return <Badge variant="outline">{severity}</Badge>;
  }
}

function getWarningTypeBadge(type: string) {
  const formatted = type.replace(/_/g, " ");
  return (
    <Badge variant="secondary" className="font-mono text-xs">
      {formatted}
    </Badge>
  );
}

function WarningCard({ warning, index }: { warning: WarningDetail; index: number }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="hover:shadow-md transition-shadow">
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <CardTitle className="text-base">
                    {warning.component_name}
                    {warning.component_version && (
                      <span className="text-sm text-muted-foreground font-normal ml-2">
                        v{warning.component_version}
                      </span>
                    )}
                  </CardTitle>
                  {getSeverityBadge(warning.severity)}
                  {getWarningTypeBadge(warning.warning_type)}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">License:</span>
                  <Badge variant="outline" className="font-mono text-xs">
                    {warning.license}
                  </Badge>
                </div>
                <CardDescription>{warning.message}</CardDescription>
              </div>
              <Button variant="ghost" size="sm">
                {isOpen ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="space-y-4 pt-0">
            <div className="space-y-3">
              <div>
                <h4 className="text-sm font-semibold mb-2">Explanation</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {warning.explanation}
                </p>
              </div>
              <div>
                <h4 className="text-sm font-semibold mb-2">Recommendations</h4>
                <div className="text-sm text-muted-foreground leading-relaxed">
                  {warning.recommendation.split(/\d+\./).filter(Boolean).map((rec, i) => (
                    <div key={i} className="flex gap-2 mb-1">
                      <span className="font-medium">{i + 1}.</span>
                      <span>{rec.trim()}</span>
                    </div>
                  ))}
                </div>
              </div>
              {warning.learn_more_url && (
                <div>
                  <a
                    href={warning.learn_more_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary hover:underline inline-flex items-center gap-1"
                  >
                    Learn More
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              )}
            </div>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

export default function ScanWarningsPage() {
  const params = useParams();
  const router = useRouter();
  const scanId = params.id as string;

  const [filterType, setFilterType] = useState<string>("all");
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const { data: warnings, isLoading, error } = useQuery({
    queryKey: ["scan-warnings", scanId],
    queryFn: () => getScanWarnings(scanId),
    retry: 1,
  });

  if (isLoading) {
    return (
      <ContentLayout title="Scan Warnings">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </ContentLayout>
    );
  }

  if (error || !warnings) {
    return (
      <ContentLayout title="Scan Warnings">
        <div className="flex flex-col items-center justify-center py-12 space-y-3">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <p className="text-sm text-muted-foreground">
            Failed to load warnings. The scan may not exist or there was an error.
          </p>
          <Button variant="outline" onClick={() => router.push(`/scans/${scanId}`)}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Scan
          </Button>
        </div>
      </ContentLayout>
    );
  }

  // Filter warnings
  const filteredWarnings = warnings.warnings.filter((w) => {
    const matchesType = filterType === "all" || w.warning_type === filterType;
    const matchesSeverity = filterSeverity === "all" || w.severity === filterSeverity;
    const matchesSearch =
      !searchQuery ||
      w.component_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      w.license.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSeverity && matchesSearch;
  });

  return (
    <ContentLayout title="Scan Warnings">
      <div className="space-y-6">
        {/* Back Button */}
        <Button variant="outline" onClick={() => router.push(`/scans/${scanId}`)}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Scan
        </Button>

        {/* Summary Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-600" />
              {warnings.total_warnings} Warning{warnings.total_warnings !== 1 ? "s" : ""} Found
            </CardTitle>
            <CardDescription>
              Detailed analysis of license warnings and recommendations
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* By Type */}
              <div>
                <p className="text-sm font-medium mb-2">By Type</p>
                <div className="space-y-1">
                  {Object.entries(warnings.by_type).map(([type, count]) => (
                    <div key={type} className="flex justify-between text-sm">
                      <span className="text-muted-foreground capitalize">
                        {type.replace(/_/g, " ")}
                      </span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* By Severity */}
              <div>
                <p className="text-sm font-medium mb-2">By Severity</p>
                <div className="space-y-1">
                  {Object.entries(warnings.by_severity).map(([severity, count]) => (
                    <div key={severity} className="flex justify-between text-sm">
                      <span className="text-muted-foreground capitalize">{severity}</span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Filters */}
        {warnings.total_warnings > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Filter Warnings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Type</label>
                  <Select value={filterType} onValueChange={setFilterType}>
                    <SelectTrigger>
                      <SelectValue placeholder="All types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All types</SelectItem>
                      {Object.keys(warnings.by_type).map((type) => (
                        <SelectItem key={type} value={type}>
                          {type.replace(/_/g, " ")} ({warnings.by_type[type]})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Severity</label>
                  <Select value={filterSeverity} onValueChange={setFilterSeverity}>
                    <SelectTrigger>
                      <SelectValue placeholder="All severities" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All severities</SelectItem>
                      {Object.keys(warnings.by_severity).map((severity) => (
                        <SelectItem key={severity} value={severity}>
                          {severity} ({warnings.by_severity[severity]})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Search</label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Component or license..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>
              </div>

              {/* Active Filters Summary */}
              {(filterType !== "all" || filterSeverity !== "all" || searchQuery) && (
                <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                  <span>
                    Showing {filteredWarnings.length} of {warnings.total_warnings} warnings
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setFilterType("all");
                      setFilterSeverity("all");
                      setSearchQuery("");
                    }}
                  >
                    Clear filters
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Warnings List */}
        {filteredWarnings.length === 0 ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center text-muted-foreground">
                {warnings.total_warnings === 0 ? (
                  <p>No warnings found for this scan.</p>
                ) : (
                  <p>No warnings match your filters.</p>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredWarnings.map((warning, index) => (
              <WarningCard key={index} warning={warning} index={index} />
            ))}
          </div>
        )}
      </div>
    </ContentLayout>
  );
}
