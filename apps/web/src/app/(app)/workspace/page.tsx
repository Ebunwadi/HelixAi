"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import {
  apiFetch,
  apiStream,
  type Conversation,
  type InvestigationInterpretResponse,
  type Message,
  readServerSentEvents,
} from "@/lib/api";

export default function WorkspacePage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [streamingText, setStreamingText] = useState("");
  const [intent, setIntent] = useState<InvestigationInterpretResponse | null>(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load the user's available conversation containers when the workspace opens.
  useEffect(() => {
    let cancelled = false;
    apiFetch<Conversation[]>("/api/v1/conversations")
      .then((items) => {
        if (!cancelled) {
          setConversations(items);
          setConversationId((current) => current || items[0]?.id || "");
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : "Could not load conversations");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  // Whenever the selected conversation changes, reload its persisted messages.
  useEffect(() => {
    if (!conversationId) {
      return;
    }

    let cancelled = false;
    apiFetch<Message[]>(`/api/v1/conversations/${conversationId}/messages`)
      .then((items) => {
        if (!cancelled) {
          setMessages(items);
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : "Could not load messages");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  // A user can type before manually creating a conversation. In that case,
  // create the container lazily just before the first message is sent.
  async function ensureConversation(): Promise<string> {
    if (conversationId) {
      return conversationId;
    }

    const conversation = await apiFetch<Conversation>("/api/v1/conversations", {
      method: "POST",
      body: JSON.stringify({ title: "AI Workspace" }),
    });
    setConversations((current) => [conversation, ...current]);
    setConversationId(conversation.id);
    return conversation.id;
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || sending) {
      return;
    }

    setSending(true);
    setError(null);
    setIntent(null);
    setStreamingText("");
    setDraft("");

    try {
      const activeConversationId = await ensureConversation();
      const response = await apiStream(
        `/api/v1/conversations/${activeConversationId}/messages/stream`,
        {
          method: "POST",
          body: JSON.stringify({ content }),
        },
      );

      // The backend emits named SSE events. We update different pieces of UI
      // state depending on whether a message was saved, text streamed, or finished.
      for await (const serverEvent of readServerSentEvents(response)) {
        if (serverEvent.event === "message.created") {
          setMessages((current) => [...current, serverEvent.data as Message]);
        } else if (serverEvent.event === "token.delta") {
          const payload = serverEvent.data as { delta: string };
          setStreamingText((current) => current + payload.delta);
        } else if (serverEvent.event === "message.completed") {
          setMessages((current) => [...current, serverEvent.data as Message]);
          setStreamingText("");
        } else if (serverEvent.event === "error") {
          const payload = serverEvent.data as { message?: string };
          throw new Error(payload.message ?? "Model streaming failed");
        }
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not send message");
    } finally {
      setSending(false);
    }
  }

  // Structured intent uses the same text but asks the backend for a typed
  // InvestigationIntent instead of a normal conversational response.
  async function interpretDraft() {
    const content = draft.trim();
    if (!content) {
      return;
    }

    setError(null);
    try {
      const result = await apiFetch<InvestigationInterpretResponse>(
        "/api/v1/ai/interpret-investigation",
        {
          method: "POST",
          body: JSON.stringify({ text: content }),
        },
      );
      setIntent(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not interpret request");
    }
  }

  // Clear state belonging to the previous conversation before loading the next one.
  function selectConversation(nextId: string) {
    setMessages([]);
    setStreamingText("");
    setIntent(null);
    setConversationId(nextId);
  }

  return (
    <section>
      <p className="eyebrow">AI Workspace · Sprint 3</p>
      <h2 className="page-title">Direct model calls, before agent frameworks.</h2>
      <p className="page-lead">
        This workspace sends conversation history directly through HelixAI&apos;s model gateway.
        Local development uses the deterministic mock provider until Azure OpenAI is configured.
      </p>

      <div className="workspace-toolbar">
        <label>
          Conversation
          <select
            value={conversationId}
            onChange={(event) => selectConversation(event.target.value)}
          >
            <option value="">New conversation on first message</option>
            {conversations.map((conversation) => (
              <option key={conversation.id} value={conversation.id}>
                {conversation.title}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="chat-panel">
        {messages.length === 0 && !streamingText ? (
          <p className="muted">No messages yet. Try: “Investigate Acme&apos;s SSO issue.”</p>
        ) : null}

        {messages.map((message) => (
          <article
            key={message.id}
            className={message.role === "user" ? "chat-message chat-user" : "chat-message"}
          >
            <span className="chat-role">{message.role}</span>
            <p>{message.content}</p>
            {message.role === "assistant" && message.model_name ? (
              <div className="model-meta">
                <span>{message.model_name}</span>
                <span>
                  tokens {message.input_tokens ?? "?"} → {message.output_tokens ?? "?"}
                </span>
                <span>{message.latency_ms ?? "?"} ms</span>
              </div>
            ) : null}
          </article>
        ))}

        {streamingText ? (
          <article className="chat-message">
            <span className="chat-role">assistant · streaming</span>
            <p>{streamingText}</p>
          </article>
        ) : null}
      </div>

      <form className="composer" onSubmit={sendMessage}>
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask HelixAI something..."
          rows={4}
        />
        <div className="composer-actions">
          <button type="button" className="secondary-button" onClick={interpretDraft}>
            Interpret as structured intent
          </button>
          <button type="submit" disabled={sending}>
            {sending ? "Streaming…" : "Send"}
          </button>
        </div>
      </form>

      {error ? <p className="error-text">{error}</p> : null}

      {intent ? (
        <section className="intent-card">
          <div>
            <p className="eyebrow">Structured output</p>
            <h3>InvestigationIntent</h3>
          </div>
          <pre>{JSON.stringify(intent.intent, null, 2)}</pre>
          <div className="model-meta">
            <span>{intent.model.model}</span>
            <span>
              tokens {intent.model.input_tokens ?? "?"} → {intent.model.output_tokens ?? "?"}
            </span>
            <span>{intent.model.latency_ms} ms</span>
          </div>
        </section>
      ) : null}
    </section>
  );
}
