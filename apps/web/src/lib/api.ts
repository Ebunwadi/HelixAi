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

export type Message = {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  model_name: string | null;
  provider_response_id: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  latency_ms: number | null;
  created_at: string;
};

export type InvestigationIntent = {
  customer_name: string | null;
  issue_type: string;
  time_reference: string | null;
  requested_actions: string[];
  summary: string;
};

export type InvestigationInterpretResponse = {
  intent: InvestigationIntent;
  model: {
    model: string;
    response_id: string | null;
    input_tokens: number | null;
    output_tokens: number | null;
    latency_ms: number;
  };
};

export type ServerSentEvent = {
  event: string;
  data: unknown;
};

// NEXT_PUBLIC_* values are intentionally browser-visible. The API URL is safe to
// expose; secrets such as Azure API keys must never be placed in these variables.
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8001";

function authHeaders(): HeadersInit {
  const mode = process.env.NEXT_PUBLIC_HELIX_AUTH_MODE ?? "dev";

  // Sprint 3 still uses the explicit local auth adapter in the browser.
  // Production token acquisition will replace this branch later.
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

async function errorFromResponse(response: Response): Promise<Error> {
  const body = (await response.json().catch(() => null)) as
    | { message?: string; correlation_id?: string }
    | null;

  // Include the API correlation ID when available so a UI error can be matched
  // to the corresponding server-side logs.
  const suffix = body?.correlation_id ? ` (${body.correlation_id})` : "";
  return new Error(`${body?.message ?? `Request failed with ${response.status}`}${suffix}`);
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  // Centralizing ordinary API calls ensures every request gets the same auth and
  // JSON headers instead of repeating that logic in individual React pages.
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw await errorFromResponse(response);
  }

  return (await response.json()) as T;
}

export async function apiStream(path: string, init?: RequestInit): Promise<Response> {
  // Streaming requests still use fetch because this endpoint is POST-based.
  // We read the returned text/event-stream body manually below.
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...authHeaders(),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw await errorFromResponse(response);
  }

  return response;
}

export async function* readServerSentEvents(
  response: Response,
): AsyncGenerator<ServerSentEvent> {
  if (!response.body) {
    throw new Error("Streaming response did not include a body.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();

    // Network chunks do not necessarily line up with SSE event boundaries, so
    // append each chunk to a buffer until a complete "\n\n" frame is available.
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done }).replaceAll(
      "\r\n",
      "\n",
    );

    let boundary = buffer.indexOf("\n\n");
    while (boundary >= 0) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      boundary = buffer.indexOf("\n\n");

      let event = "message";
      const dataLines: string[] = [];

      // A single SSE frame can contain an explicit event name and one or more
      // data lines. We normalize them into { event, data } for the workspace.
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) {
          event = line.slice("event:".length).trim();
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice("data:".length).trim());
        }
      }

      if (dataLines.length > 0) {
        yield {
          event,
          data: JSON.parse(dataLines.join("\n")) as unknown,
        };
      }
    }

    if (done) {
      break;
    }
  }
}
