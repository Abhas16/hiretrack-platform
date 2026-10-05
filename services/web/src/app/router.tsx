import { createBrowserRouter, Navigate } from "react-router";

import { AppLayout } from "@/components/layout/AppLayout";
import { LoginPage } from "@/features/auth/LoginPage";
import { RequireAuth } from "@/features/auth/RequireAuth";

/**
 * Each page is lazy-loaded: its code (and heavy libraries like charts or drag-and-drop)
 * is downloaded only when you first open that page, so the login screen loads fast.
 */
export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    children: [
      {
        index: true,
        lazy: () =>
          import("@/features/dashboard/DashboardPage").then((m) => ({
            Component: m.DashboardPage,
          })),
      },
      {
        path: "board",
        lazy: () => import("@/features/board/BoardPage").then((m) => ({ Component: m.BoardPage })),
      },
      {
        path: "review-queue",
        lazy: () =>
          import("@/features/review-queue/ReviewQueuePage").then((m) => ({
            Component: m.ReviewQueuePage,
          })),
      },
      {
        path: "applications",
        lazy: () =>
          import("@/features/applications/ApplicationsPage").then((m) => ({
            Component: m.ApplicationsPage,
          })),
      },
      {
        path: "practice",
        lazy: () =>
          import("@/features/practice/PracticePage").then((m) => ({ Component: m.PracticePage })),
      },
      {
        path: "practice/:sessionId",
        lazy: () =>
          import("@/features/practice/PracticeSessionPage").then((m) => ({
            Component: m.PracticeSessionPage,
          })),
      },
      {
        path: "analytics",
        lazy: () =>
          import("@/features/analytics/AnalyticsPage").then((m) => ({
            Component: m.AnalyticsPage,
          })),
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
