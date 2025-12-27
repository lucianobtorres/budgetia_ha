import { useLocation, useOutlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { BottomNav } from "../components/layout/BottomNav";
import { OfflineIndicator } from "../components/ui/OfflineIndicator";
import { AnimatePresence, motion } from "framer-motion";

export function Layout() {
  const location = useLocation();
  const element = useOutlet();

  return (
    <div className="relative flex h-[100dvh] w-full max-w-[100vw] flex-col md:flex-row bg-gray-950 text-gray-100 font-sans antialiased overflow-hidden">
      <div className="absolute top-0 left-0 right-0 z-50">
        <OfflineIndicator />
      </div>

      <Sidebar />
      <main className="flex-1 overflow-y-auto overflow-x-hidden bg-gray-950 p-4 pb-20 md:p-8 md:pb-8 w-full">
        <div className="mx-auto max-w-7xl w-full h-full">
            <AnimatePresence mode="wait">
                <motion.div
                    key={location.pathname}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.3, ease: 'easeInOut' }}
                    className="h-full"
                >
                    {element}
                </motion.div>
            </AnimatePresence>
        </div>
      </main>
      <BottomNav />
    </div>
  );
}
