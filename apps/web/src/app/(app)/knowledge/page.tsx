"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import {
  apiFetch,
  apiUpload,
  type KnowledgeBase,
  type KnowledgeDocument,
  type RagAnswer,
} from "@/lib/api";

export default function KnowledgePage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [newName, setNewName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<RagAnswer | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadKnowledgeBases() {
    const items = await apiFetch<KnowledgeBase[]>("/api/v1/knowledge-bases");
    setKnowledgeBases(items);
    setSelectedId((current) => current || items[0]?.id || "");
  }

  async function loadDocuments(knowledgeBaseId: string) {
    const items = await apiFetch<KnowledgeDocument[]>(
      `/api/v1/knowledge-bases/${knowledgeBaseId}/documents`,
    );
    setDocuments(items);
  }

  useEffect(() => {
    let cancelled = false;

    apiFetch<KnowledgeBase[]>("/api/v1/knowledge-bases")
      .then((items) => {
        if (!cancelled) {
          setKnowledgeBases(items);
          setSelectedId((current) => current || items[0]?.id || "");
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : "Could not load knowledge bases");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedId) {
      return;
    }

    let cancelled = false;
    apiFetch<KnowledgeDocument[]>(`/api/v1/knowledge-bases/${selectedId}/documents`)
      .then((items) => {
        if (!cancelled) {
          setDocuments(items);
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : "Could not load documents");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  async function createKnowledgeBase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newName.trim()) {
      return;
    }

    setError(null);
    try {
      const created = await apiFetch<KnowledgeBase>("/api/v1/knowledge-bases", {
        method: "POST",
        body: JSON.stringify({ name: newName.trim() }),
      });
      setNewName("");
      await loadKnowledgeBases();
      setSelectedId(created.id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not create knowledge base");
    }
  }

  async function uploadDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId || !file) {
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      await apiUpload<KnowledgeDocument>(
        `/api/v1/knowledge-bases/${selectedId}/documents`,
        form,
      );
      setFile(null);
      await loadDocuments(selectedId);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not upload document");
    } finally {
      setBusy(false);
    }
  }

  async function askKnowledge(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId || !question.trim()) {
      return;
    }

    setBusy(true);
    setError(null);
    setAnswer(null);
    try {
      const result = await apiFetch<RagAnswer>(
        `/api/v1/knowledge-bases/${selectedId}/answer`,
        {
          method: "POST",
          body: JSON.stringify({ question: question.trim() }),
        },
      );
      setAnswer(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not answer question");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <p className="eyebrow">Sprint 4 · Baseline RAG</p>
      <h2 className="page-title">Knowledge</h2>
      <p className="page-lead">
        Upload a small text, Markdown or PDF document. HelixAI extracts, chunks, embeds and
        indexes it, then retrieves evidence before asking the model to answer.
      </p>

      <div className="knowledge-grid">
        <section className="knowledge-panel">
          <h3>Knowledge bases</h3>
          <form className="inline-form" onSubmit={createKnowledgeBase}>
            <input
              value={newName}
              onChange={(event) => setNewName(event.target.value)}
              placeholder="New knowledge base"
            />
            <button type="submit">Create</button>
          </form>

          <label className="field-label">
            Active knowledge base
            <select
              value={selectedId}
              onChange={(event) => {
                setDocuments([]);
                setAnswer(null);
                setSelectedId(event.target.value);
              }}
            >
              <option value="">Select one</option>
              {knowledgeBases.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>

          <form className="stack-form" onSubmit={uploadDocument}>
            <label className="field-label">
              Upload source document
              <input
                type="file"
                accept=".txt,.md,.pdf"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </label>
            <button type="submit" disabled={!selectedId || !file || busy}>
              {busy ? "Working…" : "Upload & index"}
            </button>
          </form>

          <div className="card-list">
            {documents.map((document) => (
              <article className="data-card" key={document.id}>
                <div>
                  <strong>{document.filename}</strong>
                  <p>
                    {document.chunk_count} chunks · {document.status}
                  </p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="knowledge-panel">
          <h3>Ask the knowledge base</h3>
          <form className="stack-form" onSubmit={askKnowledge}>
            <textarea
              rows={5}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="What does the uploaded documentation say?"
            />
            <button type="submit" disabled={!selectedId || busy}>
              {busy ? "Retrieving…" : "Retrieve & answer"}
            </button>
          </form>

          {error ? <p className="error-text">{error}</p> : null}

          {answer ? (
            <div className="rag-answer">
              <p>{answer.answer}</p>
              <h4>Citations</h4>
              {answer.citations.map((citation) => (
                <article className="citation-card" key={citation.chunk_id}>
                  <strong>
                    [{citation.number}] {citation.filename} · chunk {citation.chunk_index}
                  </strong>
                  <p>{citation.excerpt}</p>
                  <span>score {citation.score.toFixed(3)}</span>
                </article>
              ))}
            </div>
          ) : null}
        </section>
      </div>
    </section>
  );
}
