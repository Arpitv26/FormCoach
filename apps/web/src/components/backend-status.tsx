"use client";

import { useState } from "react";
import { api } from "@/lib/api/client";

export function BackendStatus() {
  const [status, setStatus] = useState("Not checked. The demo works without the backend.");
  const [checking, setChecking] = useState(false);

  async function checkHealth() {
    setChecking(true);
    try {
      const health = await api.health();
      setStatus(`${health.service}: ${health.status}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not check the backend.");
    } finally {
      setChecking(false);
    }
  }

  return (
    <details className="connection-details">
      <summary>Connection tools <span className="muted">Optional for this demo</span></summary>
      <div className="connection-content">
        <p role="status">{status}</p>
        <button onClick={checkHealth} disabled={checking}>
          {checking ? "Checking…" : "Check backend health"}
        </button>
      </div>
    </details>
  );
}
