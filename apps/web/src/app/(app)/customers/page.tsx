"use client";

import { useEffect, useState } from "react";

import { apiFetch, type Customer } from "@/lib/api";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Customer[]>("/api/v1/customers")
      .then(setCustomers)
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Could not load customers");
      });
  }, []);

  return (
    <section>
      <p className="eyebrow">Tenant-scoped data</p>
      <h2 className="page-title">Customers</h2>
      <p className="page-lead">
        This list comes from an API query that always includes the authenticated tenant ID.
      </p>
      {error ? <p className="error-text">{error}</p> : null}
      <div className="card-list">
        {customers.map((customer) => (
          <article className="data-card" key={customer.id}>
            <div>
              <strong>{customer.name}</strong>
              <p>{customer.external_ref ?? "No external reference"}</p>
            </div>
            <div className="data-meta">
              <span>{customer.subscription_plan ?? "No plan"}</span>
              <span>{customer.region ?? "No region"}</span>
              <span>{customer.status}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
