import { Toaster } from "sonner";
import { Routes, Route, Navigate } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/react-query";

import { Layout } from "./layouts/Layout";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Profile from "./pages/Profile";
import Intelligence from "./pages/Intelligence";
import Transactions from "./pages/Transactions";
import Notifications from "./pages/Notifications";
import Onboarding from "./pages/Onboarding";
import GoogleCallback from "./pages/GoogleCallback";
import Connections from "./pages/Connections";
import Admin from "./pages/Admin";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import VerifyEmail from "./pages/VerifyEmail"; // <--- Restored
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";

import { useAuthSession } from "./hooks/useAuthSession";
import { DrawerProvider } from "./context/DrawerContext";
import { GlobalDrawers } from "./components/layout/GlobalDrawers";
import { TourProvider } from "./context/TourContext";

import ConnectionErrorPage from "./pages/ConnectionErrorPage";
import Landing from "./pages/Landing";

function App() {
  const { user, onboardingStatus, handleLogin } = useAuthSession();

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
                    {/* Public Routes */}
                    <Route path="/landing" element={<Landing />} />
                    <Route path="/login" element={
                        user ? <Navigate to="/" replace /> : <Login onLogin={handleLogin} />
                    } />
                    <Route path="/verify" element={<VerifyEmail />} />
                    <Route path="/forgot-password" element={<ForgotPassword />} />
                    <Route path="/reset-password" element={<ResetPassword />} />
                    <Route path="/google-callback" element={<GoogleCallback />} />

                    {/* Onboarding Route (Protected but separate from Layout) */}
                    <Route path="/onboarding" element={
                        !user ? <Navigate to="/login" replace /> :
                        onboardingStatus === 'COMPLETE' ? <Navigate to="/" replace /> : <Onboarding />
                    } />

                    {/* Protected Application Routes */}
                    <Route path="/" element={
                        !user ? <Navigate to="/login" replace /> : <Layout />
                    }>
                        <Route index element={<Dashboard />} />
                        <Route path="chat" element={<Chat />} />
                        <Route path="transactions" element={<Transactions />} />
                        <Route path="notifications" element={<Notifications />} />
                        <Route path="connections" element={<Connections />} />
                        <Route path="profile" element={<Profile />} />
                        <Route path="intelligence" element={<Intelligence />} />
                        <Route path="admin" element={<Admin />} />
                        <Route path="*" element={<NotFound />} />
                    </Route>
                </Routes>
            </TourProvider>
        </DrawerProvider>
    </QueryClientProvider>
  );
}

export default App;
