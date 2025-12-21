import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";

export function Layout() {
  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 font-sans antialiased overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-auto bg-gray-950 p-8">
        <div className="mx-auto max-w-7xl">
            <Outlet />
        </div>
      </main>
    </div>
  );
}
