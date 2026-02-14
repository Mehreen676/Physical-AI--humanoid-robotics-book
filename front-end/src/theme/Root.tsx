import React, { useEffect, useRef, useState } from "react";
import type { Props } from "@theme/Root";

type Msg = { role: "user" | "assistant"; content: string };

function getSelectedText() {
  try {
    const t = window.getSelection()?.toString() ?? "";
    return t.trim();
  } catch {
    return "";
  }
}

export default function Root({ children }: Props) {
  const API_URL =
    (typeof window !== "undefined" && (window as any).__RAG_API_URL__) ||
    "http://127.0.0.1:8000/api/v1/chat";

  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState("");
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: "assistant", content: "Hi! Ask me anything about this textbook." },
  ]);

  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const id = window.setInterval(() => setSelected(getSelectedText()), 400);
    return () => window.clearInterval(id);
  }, [open]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [msgs, open]);

  async function send() {
    const q = input.trim();
    if (!q || busy) return;

    const sel = selected.trim();
    const useSelected = sel.length > 0;

    setMsgs((m) => [...m, { role: "user", content: q }]);
    setInput("");
    setBusy(true);

    try {
      const payload: any = {
        question: q,
        retrieval_mode: useSelected ? "selected_text" : "normal",
      };
      if (useSelected) payload.selected_text = sel;

      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));
      const answer =
        data.answer ||
        data.response ||
        data.message ||
        (typeof data === "string" ? data : "") ||
        "No response";

      setMsgs((m) => [...m, { role: "assistant", content: String(answer) }]);
    } catch (e: any) {
      setMsgs((m) => [
        ...m,
        { role: "assistant", content: `Error: ${e?.message || "Failed to reach backend"}` },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {children}

      {/* Floating Robot Button */}
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          position: "fixed",
          right: 22,
          bottom: 22,
          zIndex: 9999,
          width: 64,
          height: 64,
          borderRadius: "50%",
          border: "1px solid rgba(0,255,255,0.4)",
          background: "linear-gradient(145deg, #00c6ff, #0072ff)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          boxShadow: "0 0 20px rgba(0,200,255,0.6)",
          transition: "all 0.3s ease",
          userSelect: "none",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = "scale(1.1)";
          e.currentTarget.style.boxShadow = "0 0 30px rgba(0,255,255,0.9)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "scale(1)";
          e.currentTarget.style.boxShadow = "0 0 20px rgba(0,200,255,0.6)";
        }}
        aria-label="Open chatbot"
        title={open ? "Close Chatbot" : "Open Chatbot"}
      >
        <span style={{ fontSize: 28, filter: "drop-shadow(0 0 10px rgba(255,255,255,0.35))" }}>
          🤖
        </span>
      </button>

      {/* Chat Panel */}
      {open && (
        <div
          style={{
            position: "fixed",
            right: 22,
            bottom: 96,
            width: 380,
            maxWidth: "calc(100vw - 44px)",
            height: 540,
            maxHeight: "calc(100vh - 140px)",
            zIndex: 9999,
            borderRadius: 18,
            overflow: "hidden",
            border: "1px solid rgba(0,255,255,0.18)",
            background: "rgba(8, 18, 36, 0.92)",
            color: "white",
            boxShadow: "0 18px 60px rgba(0,0,0,0.45)",
            display: "flex",
            flexDirection: "column",
            backdropFilter: "blur(8px)",
          }}
        >
          <div
            style={{
              padding: 12,
              borderBottom: "1px solid rgba(255,255,255,0.10)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 10,
            }}
          >
            <div>
              <div style={{ fontWeight: 800, letterSpacing: 0.2 }}>Physical AI Chatbot</div>
              <div style={{ fontSize: 12, opacity: 0.75 }}>API: {API_URL}</div>
              <div style={{ fontSize: 12, opacity: 0.85, marginTop: 6 }}>
                {selected ? "Selected text detected ✅" : "Select text to use selected_text mode"}
              </div>
            </div>

            <button
              onClick={() => setOpen(false)}
              style={{
                borderRadius: 12,
                padding: "8px 10px",
                border: "1px solid rgba(255,255,255,0.15)",
                background: "rgba(255,255,255,0.06)",
                color: "white",
                cursor: "pointer",
                fontWeight: 700,
              }}
              aria-label="Close chatbot"
              title="Close"
            >
              ✕
            </button>
          </div>

          <div
            ref={listRef}
            style={{
              padding: 12,
              flex: 1,
              overflow: "auto",
              display: "flex",
              flexDirection: "column",
              gap: 10,
            }}
          >
            {msgs.map((m, i) => (
              <div
                key={i}
                style={{
                  alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                  maxWidth: "92%",
                  padding: "10px 12px",
                  borderRadius: 14,
                  background:
                    m.role === "user"
                      ? "rgba(0, 198, 255, 0.18)"
                      : "rgba(255,255,255,0.08)",
                  border:
                    m.role === "user"
                      ? "1px solid rgba(0,255,255,0.20)"
                      : "1px solid rgba(255,255,255,0.10)",
                  whiteSpace: "pre-wrap",
                  lineHeight: 1.35,
                }}
              >
                {m.content}
              </div>
            ))}
          </div>

          <div style={{ padding: 12, borderTop: "1px solid rgba(255,255,255,0.10)" }}>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder={busy ? "Thinking..." : "Ask a question..."}
                style={{
                  flex: 1,
                  padding: "10px 12px",
                  borderRadius: 12,
                  border: "1px solid rgba(255,255,255,0.14)",
                  background: "rgba(0,0,0,0.25)",
                  color: "white",
                  outline: "none",
                }}
                disabled={busy}
              />
              <button
                onClick={send}
                disabled={busy || !input.trim()}
                style={{
                  padding: "10px 12px",
                  borderRadius: 12,
                  border: "1px solid rgba(0,255,255,0.22)",
                  background: busy ? "rgba(255,255,255,0.08)" : "rgba(0, 198, 255, 0.22)",
                  color: "white",
                  cursor: busy ? "not-allowed" : "pointer",
                  fontWeight: 800,
                  minWidth: 78,
                }}
              >
                Send
              </button>
            </div>

            <div style={{ fontSize: 12, opacity: 0.75, marginTop: 8 }}>
              Tip: text select karo → phir question bhejo → selected_text mode use hoga.
            </div>
          </div>
        </div>
      )}
    </>
  );
}
