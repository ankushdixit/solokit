"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LayoutDashboard } from "lucide-react";

/**
 * Dashboard home page
 *
 * This is a minimal starting point. Add your dashboard widgets
 * and statistics as you build your application.
 *
 * See ARCHITECTURE.md for patterns on:
 * - Adding resource pages
 * - Using Refine hooks (useList, useTable)
 * - Building dashboard widgets
 */
export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Welcome to Refine Dashboard</h1>
        <p className="text-muted-foreground">
          Your Refine.dev admin dashboard is ready. Start building!
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center space-y-0 pb-2">
            <CardTitle className="text-lg font-medium">Getting Started</CardTitle>
            <LayoutDashboard className="ml-auto h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>Read ARCHITECTURE.md to understand the dashboard patterns.</p>
            <p>Create your PRD at docs/PRD.md to define your features.</p>
            <p>Configure your data provider in lib/refine.tsx.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center space-y-0 pb-2">
            <CardTitle className="text-lg font-medium">Next Steps</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>1. Set up your backend API connection</p>
            <p>2. Define your resources in lib/refine.tsx</p>
            <p>3. Create resource pages in app/(dashboard)/</p>
            <p>4. Add navigation items to the sidebar</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
