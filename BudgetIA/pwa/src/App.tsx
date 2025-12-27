import { Toaster } from "sonner";
import { Routes, Route, Navigate } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/react-query";

import { Layout } from "./layouts/Layout";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Profile from "./pages/Profile";
import Transactions from "./pages/Transactions";
import Notifications from "./pages/Notifications";
import Onboarding from "./pages/Onboarding";
import GoogleCallback from "./pages/GoogleCallback";
import Connections from "./pages/Connections";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";

import { useAuthSession } from "./hooks/useAuthSession";
import { DrawerProvider } from "./context/DrawerContext";
import { GlobalDrawers } from "./components/layout/GlobalDrawers";
import { TourProvider } from "./context/TourContext";

import ConnectionErrorPage from "./pages/ConnectionErrorPage";

function App() {
  const { user, onboardingStatus, handleLogin } = useAuthSession();

  if (!user) {
      return <Login onLogin={handleLogin} />;
  }

  if (onboardingStatus === 'ERROR') {
      return <ConnectionErrorPage onRetry={() => window.location.reload()} />;
  }

  return (
    <QueryClientProvider client={queryClient}>
        <DrawerProvider>
            <TourProvider>
                <Toaster position="top-right" theme="dark" richColors />
                <GlobalDrawers />
                <Routes>
                <Route path="/onboarding" element={
                    onboardingStatus === 'COMPLETE' ? <Navigate to="/" replace /> : <Onboarding />
                } />
                <Route path="/google-callback" element={<GoogleCallback />} />
                <Route path="/" element={<Layout />}>
                    <Route index element={<Dashboard />} />
                    <Route path="chat" element={<Chat />} />
                    <Route path="transactions" element={<Transactions />} />
                    <Route path="notifications" element={<Notifications />} />
                    <Route path="connections" element={<Connections />} />
                    <Route path="profile" element={<Profile />} />
                    <Route path="*" element={<NotFound />} />
                </Route>
                </Routes>
            </TourProvider>
        </DrawerProvider>
    </QueryClientProvider>
  );
}

export default App;
