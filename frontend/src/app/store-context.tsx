import { createContext, type ReactNode, useContext, useRef, useSyncExternalStore } from "react";
import type { CareTask } from "../entities/care-task/model";
import type { DashboardSummary } from "../entities/dashboard/model";
import type { Event } from "../entities/event/model";
import type { PetSummary } from "../entities/pet/model";
import { createHerpRepository, type HerpRepository } from "../mocks/repository";

const StoreContext = createContext<HerpRepository | null>(null);

export function AppStoreProvider({ children }: { children: ReactNode }) {
  const storeRef = useRef<HerpRepository>();
  if (!storeRef.current) {
    storeRef.current = createHerpRepository();
  }

  return <StoreContext.Provider value={storeRef.current}>{children}</StoreContext.Provider>;
}

export function useHerpStore(): HerpRepository {
  const store = useContext(StoreContext);
  if (!store) {
    throw new Error("useHerpStore must be used within AppStoreProvider");
  }
  return store;
}

export function useHerpSnapshot(): {
  pets: readonly PetSummary[];
  events: readonly Event[];
  careTasks: readonly CareTask[];
  dashboard: DashboardSummary;
} {
  const store = useHerpStore();
  useSyncExternalStore(store.subscribe, store.getVersion, store.getVersion);
  return {
    pets: store.getPets(),
    events: store.getEvents(),
    careTasks: store.getCareTasks(),
    dashboard: store.getDashboardSummary(),
  };
}
