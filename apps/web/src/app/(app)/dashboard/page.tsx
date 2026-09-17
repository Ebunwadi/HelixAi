"use client";

import { useCurrentContext } from "@/components/protected-shell";

export default function DashboardPage() {
  const context = useCurrentContext();

  return (
    <section>
      <p className="eyebrow">Sprint 2 · SaaS foundation</p>
      <h2 className="page-title">Welcome to {context.tenant_name}</h2>
      <p className="page-lead">
        Your authenticated identity has been mapped to an active HelixAI tenant membership.
      </p>
      <div className="stat-grid">
        <article className="stat-card">
          <span>Role</span>
          <strong>{context.role}</strong>
        </article>
        <article className="stat-card">
          <span>Tenant</span>
          <strong>{context.tenant_slug}</strong>
        </article>
        <article className="stat-card">
          <span>User</span>
          <strong>{context.display_name ?? context.email ?? "Provisioned user"}</strong>
        </article>
      </div>
    </section>
  );
}
