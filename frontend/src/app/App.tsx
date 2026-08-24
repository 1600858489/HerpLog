import { BrowserRouter, Navigate, Route, Routes, useInRouterContext } from "react-router-dom";
import { DashboardPage } from "../pages/dashboard-page";
import { PetsPage } from "../pages/pets-page";
import { RecordPage } from "../pages/record-page";
import { TimelinePage } from "../pages/timeline-page";
import { TodayPage } from "../pages/today-page";
import { AppShell } from "./app-shell";
import { AppStoreProvider } from "./store-context";

function AppRoutes() {
  return (
    <AppStoreProvider>
      <AppShell>
        <Routes>
          <Route path="/" element={<Navigate to="/today" replace />} />
          <Route path="/today" element={<TodayPage />} />
          <Route path="/record" element={<RecordPage />} />
          <Route path="/pets" element={<PetsPage />} />
          <Route path="/timeline" element={<TimelinePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="*" element={<Navigate to="/today" replace />} />
        </Routes>
      </AppShell>
    </AppStoreProvider>
  );
}

function AppRouter() {
  return useInRouterContext() ? <AppRoutes /> : <BrowserRouter><AppRoutes /></BrowserRouter>;
}

export function App() {
  return <AppRouter />;
}
