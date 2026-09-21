"use client";

import Link from "next/link";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import { apiFetch, type Conversation } from "@/lib/api";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiFetch<Conversation[]>("/api/v1/conversations")
      .then((items) => {
        if (!cancelled) {
          setConversations(items);
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

  async function reloadConversations() {
    setConversations(await apiFetch<Conversation[]>("/api/v1/conversations"));
  }

  async function createConversation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await apiFetch<Conversation>("/api/v1/conversations", {
        method: "POST",
        body: JSON.stringify({ title: title || "New conversation" }),
      });
      setTitle("");
      await reloadConversations();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not create conversation");
    }
  }

  return (
    <section>
      <p className="eyebrow">Conversation containers</p>
      <h2 className="page-title">Conversations</h2>
      <p className="page-lead">
        Conversations now own persisted user and assistant messages. Model calls themselves stay
        behind the Sprint 3 gateway.
      </p>
      <form className="inline-form" onSubmit={createConversation}>
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Investigation title"
          aria-label="Conversation title"
        />
        <button type="submit">Create</button>
      </form>
      {error ? <p className="error-text">{error}</p> : null}
      <div className="card-list">
        {conversations.map((conversation) => (
          <article className="data-card" key={conversation.id}>
            <div>
              <strong>{conversation.title}</strong>
              <p>{new Date(conversation.created_at).toLocaleString()}</p>
            </div>
            <div className="data-meta">
              <span>{conversation.status}</span>
              <Link href="/workspace">Open in Workspace →</Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
