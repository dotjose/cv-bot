import { create } from "zustand";

import type { NavId } from "@/lib/types";

export interface UiStore {
  /** Main column: chat messages or structured profile section */
  activeView: NavId;
  /** Mobile drawer */
  sidebarOpen: boolean;
  /** Desktop (lg+): icon-only narrow rail */
  sidebarCollapsed: boolean;

  setActiveView: (view: NavId) => void;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebarCollapsed: () => void;
}

export const useUiStore = create<UiStore>()((set) => ({
  activeView: "chat",
  sidebarOpen: false,
  sidebarCollapsed: false,

  setActiveView: (activeView) =>
    set({
      activeView,
      sidebarOpen: false,
    }),

  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),

  toggleSidebarCollapsed: () =>
    set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
}));
