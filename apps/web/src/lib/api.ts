export type MembershipRole = "operator" | "manager" | "admin";

export type CurrentContext = {
  user_id: string;
  tenant_id: string;
  role: MembershipRole;
  email: string | null;
  display_name: string | null;
  tenant_name: string;
  tenant_slug: string;
};

export type Customer = {
  id: string;
  external_ref: string | null;
  name: string;
  subscription_plan: string | null;
  region: string | null;
  status: "active" | "inactive";
  metadata: Record<string, unknown>;
};

export type Conversation = {
  id: string;
  title: string;
  status: "active" | "archived";
  created_at: string;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function authHeaders(): HeadersInit {
  const mode = process.env.NEXT_PUBLIC_HELIX_AUTH_MODE ?? "dev";

  if (mode !== "dev") {
    throw new Error(
      "Browser OIDC token acquisition is not configured. Use dev auth locally or configure the identity provider integration.",
    );
  }

  const subject = process.env.NEXT_PUBLIC_HELIX_DEV_SUBJECT;
  const tenantId = process.env.NEXT_PUBLIC_HELIX_DEV_TENANT_ID;
  if (!subject || !tenantId) {
    throw new Error("Local auth requires NEXT_PUBLIC_HELIX_DEV_SUBJECT and tenant ID.");
  }

  return {
    "X-Helix-Subject": subject,
    "X-Helix-Tenant-Id": tenantId,
    "X-Helix-Email": process.env.NEXT_PUBLIC_HELIX_DEV_EMAIL ?? "",
    "X-Helix-Name": process.env.NEXT_PUBLIC_HELIX_DEV_NAME ?? "",
  };
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as
      | { message?: string; correlation_id?: string }
      | null;
    const suffix = body?.correlation_id ? ` (${body.correlation_id})` : "";
    throw new Error(`${body?.message ?? `Request failed with ${response.status}`}${suffix}`);
  }

  return (await response.json()) as T;
}
