import { Outlet } from "react-router";

import { AddApplicationModal } from "@/features/add-application/AddApplicationModal";

import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { useAppLayoutController } from "./useAppLayoutController";

/** The signed-in shell: sidebar + top bar around whichever page the router renders. */
export function AppLayout() {
  const c = useAppLayoutController();

  return (
    <div className="flex min-h-screen flex-wrap">
      <Sidebar items={c.navItems} buildInfo={c.buildInfo} onSignOut={c.signOut} />
      <main className="flex min-w-0 flex-[999_1_560px] flex-col">
        <TopBar title={c.title} query={c.query} onSearch={c.onSearch} onAdd={c.openAdd} />
        <div className="flex flex-col gap-6 px-8 pt-7 pb-12">
          <Outlet />
        </div>
      </main>
      {c.isAddOpen && <AddApplicationModal onClose={c.closeAdd} />}
    </div>
  );
}
