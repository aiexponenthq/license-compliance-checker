"use client";

import { ContentLayout } from "@/components/admin-panel/content-layout";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Settings as SettingsIcon, Bell, Shield, Database, Trash2 } from "lucide-react";
import { Separator } from "@/components/ui/separator";

import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useState } from "react";
import { Loader2 } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export default function SettingsPage() {
  const router = useRouter();
  const [isDeleting, setIsDeleting] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  const handleDeleteAllScans = async () => {
    try {
      setIsDeleting(true);
      await api.delete("/scans");
      toast.success("All scans deleted successfully");
    } catch (error) {
      console.error("Failed to delete scans:", error);
      toast.error("Failed to delete scans");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleResetApplication = async () => {
    try {
      setIsResetting(true);
      await api.post("/admin/reset");
      toast.success("Application reset successfully");
      // Optional: Redirect to login or refresh page
      window.location.reload();
    } catch (error) {
      console.error("Failed to reset application:", error);
      toast.error("Failed to reset application");
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <ContentLayout title="Settings">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
            <p className="text-muted-foreground mt-2">
              Manage application preferences and configuration
            </p>
          </div>
        </div>

        {/* Scan Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <SettingsIcon className="h-5 w-5 text-primary" />
              <CardTitle>Scan Settings</CardTitle>
            </div>
            <CardDescription>
              Configure default scan behavior and preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="default-policy">Default Policy</Label>
              <Input
                id="default-policy"
                placeholder="permissive"
                defaultValue="permissive"
                disabled
              />
              <p className="text-xs text-muted-foreground">
                Default policy applied to new scans (currently set via CLI)
              </p>
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto-scan on commit</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically scan repositories on git commits
                </p>
              </div>
              <Switch disabled />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Enable AI/ML detection</Label>
                <p className="text-sm text-muted-foreground">
                  Detect AI models and datasets during scans
                </p>
              </div>
              <Switch defaultChecked disabled />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Deep license scanning</Label>
                <p className="text-sm text-muted-foreground">
                  Perform thorough file-level license detection
                </p>
              </div>
              <Switch defaultChecked disabled />
            </div>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-primary" />
              <CardTitle>Notifications</CardTitle>
            </div>
            <CardDescription>
              Configure notification preferences for compliance events
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Violation alerts</Label>
                <p className="text-sm text-muted-foreground">
                  Get notified when license violations are detected
                </p>
              </div>
              <Switch defaultChecked disabled />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Scan completion</Label>
                <p className="text-sm text-muted-foreground">
                  Notify when scan finishes processing
                </p>
              </div>
              <Switch disabled />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Weekly summary</Label>
                <p className="text-sm text-muted-foreground">
                  Receive weekly compliance summary reports
                </p>
              </div>
              <Switch disabled />
            </div>

            <Separator />

            <div className="space-y-2">
              <Label htmlFor="notification-email">Notification Email</Label>
              <Input
                id="notification-email"
                type="email"
                placeholder="admin@example.com"
                disabled
              />
              <p className="text-xs text-muted-foreground">
                Email address for compliance notifications
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Security Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary" />
              <CardTitle>Security</CardTitle>
            </div>
            <CardDescription>
              Manage authentication and API access
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Change Password</Label>
              <p className="text-sm text-muted-foreground mb-2">
                Update your account password
              </p>
              <Button variant="outline" onClick={() => router.push("/change-password")}>
                Change Password
              </Button>
            </div>

            <Separator />

            <div className="space-y-2">
              <Label>API Keys</Label>
              <p className="text-sm text-muted-foreground mb-2">
                Manage API keys for programmatic access
              </p>
              <Button variant="outline" disabled>
                Manage API Keys
              </Button>
              <p className="text-xs text-muted-foreground">
                Use CLI: <code className="bg-muted px-1 py-0.5 rounded">lcc auth create-key</code>
              </p>
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Session timeout</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically log out after inactivity
                </p>
              </div>
              <Switch defaultChecked disabled />
            </div>
          </CardContent>
        </Card>

        {/* Data & Storage */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-primary" />
              <CardTitle>Data & Storage</CardTitle>
            </div>
            <CardDescription>
              Manage scan data and cache settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Cache Management</Label>
              <p className="text-sm text-muted-foreground mb-2">
                Clear cached license resolution data
              </p>
              <Button variant="outline" disabled>
                Clear Cache
              </Button>
              <p className="text-xs text-muted-foreground">
                Use CLI: <code className="bg-muted px-1 py-0.5 rounded">docker exec [container] rm -rf /var/cache/lcc/</code>
              </p>
            </div>

            <Separator />

            <div className="space-y-2">
              <Label>Data Retention</Label>
              <Input
                type="number"
                placeholder="90"
                defaultValue="90"
                disabled
              />
              <p className="text-xs text-muted-foreground">
                Number of days to retain scan history
              </p>
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto-cleanup old scans</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically remove scans older than retention period
                </p>
              </div>
              <Switch disabled />
            </div>
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="border-destructive">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Trash2 className="h-5 w-5 text-destructive" />
              <CardTitle className="text-destructive">Danger Zone</CardTitle>
            </div>
            <CardDescription>
              Irreversible actions - proceed with caution
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Delete All Scans</Label>
              <p className="text-sm text-muted-foreground mb-2">
                Permanently delete all scan history and data
              </p>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" disabled={isDeleting}>
                    {isDeleting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                    Delete All Scans
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This action cannot be undone. This will permanently delete all scan history and data from the database.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={handleDeleteAllScans} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                      Delete All
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>

            <Separator />

            <div className="space-y-2">
              <Label>Reset Application</Label>
              <p className="text-sm text-muted-foreground mb-2">
                Reset application to default configuration
              </p>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" disabled={isResetting}>
                    {isResetting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                    Reset Application
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will delete all data, clear all caches, and reset the application to its initial state. This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={handleResetApplication} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                      Reset Everything
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </CardContent>
        </Card>

        {/* Info Card */}
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">
              <strong>Note:</strong> Most settings are currently configured via environment variables or CLI commands.
              Full web-based configuration management is planned for a future release.
              See the <a href="https://github.com/anthropics/license-compliance-checker" className="text-primary hover:underline">documentation</a> for configuration details.
            </p>
          </CardContent>
        </Card>
      </div>
    </ContentLayout>
  );
}
