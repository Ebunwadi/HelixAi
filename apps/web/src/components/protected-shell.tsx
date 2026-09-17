"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";

import { apiFetch, type CurrentContext } from "@/lib/api";

const CurrentContextValue = createContext<CurrentContext | null>(null);

const navigation = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/workspace", label: "AI Workspace" },
  { href: "/customers", label: "Customers" },
  { href: "/conversations", label: "Conversations" },
];

export function useCurrentContext(): CurrentContext {
  const value = useContext(CurrentContextValue);
  if (!value) {
    throw new Error("useCurrentContext must be used inside ProtectedShell");
  }
  return value;
}

export function ProtectedShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [context, setContext] = useState<CurrentContext | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadContext() {
      try {
        const current = await apiFetch<CurrentContext>("/api/v1/me");
        if (!cancelled) {
          setContext(current);
        }
      } catch (reason) {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : "Session unavailable");
        }
      }
    }

    void loadContext();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <main className="session-state">
        <div className="session-card">
          <p className="eyebrow">Authentication required</p>
          <h1>HelixAI could not establish your tenant session.</h1>
          <p>{error}</p>
          <p className="muted">
            For local Sprint 2 development, run the bootstrap command and copy the web
            environment example to <code>.env.local</code>.
          </p>
        </div>
      </main>
    );
  }

  if (!context) {
    return (
      <main className="session-state">
        <div className="session-card">
          <p className="eyebrow">HelixAI</p>
          <h1>Establishing tenant context…</h1>
        </div>
      </main>
    );
  }

  return (
    <CurrentContextValue.Provider value={context}>
      <div className="app-shell">
        <aside className="sidebar">
          <div>
            <p className="eyebrow">HelixAI</p>
            <h1 className="brand">Operations</h1>
          </div>
          <nav className="nav-list" aria-label="Primary navigation">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={pathname === item.href ? "nav-link nav-link-active" : "nav-link"}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="tenant-card">
            <strong>{context.tenant_name}</strong>
            <span>{context.role}</span>
            <span>{context.display_name ?? context.email ?? "HelixAI user"}</span>
          </div>
        </aside>
        <main className="page-content">{children}</main>
      </div>
    </CurrentContextValue.Provider>
  );
}
