import { useState } from "react";

const SAMPLE_REQUESTS = ["Please check invoice INV-1001"];

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

const EMPTY_TRACE = {
  traceId: "",
  userInput: "",
  finalAnswer: "",
  steps: [],
};

export default function App() {
  const [apiBaseUrl, setApiBaseUrl] = useState(DEFAULT_API_BASE_URL);
  const [userRequest, setUserRequest] = useState(SAMPLE_REQUESTS[0]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [runError, setRunError] = useState("");
  const [traceError, setTraceError] = useState("");
  const [result, setResult] = useState(null);
  const [trace, setTrace] = useState(EMPTY_TRACE);
  const [traceIdInput, setTraceIdInput] = useState("");
  const [copyFeedback, setCopyFeedback] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!userRequest.trim()) {
      setRunError("Please enter a user request.");
      return;
    }

    setIsSubmitting(true);
    setRunError("");
    setTraceError("");

    try {
      const runResponse = await fetch(`${normalizeApiBaseUrl(apiBaseUrl)}/agent/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ userRequest }),
      });

      const runPayload = await parseJson(runResponse);
      if (!runResponse.ok) {
        throw new Error(runPayload?.detail || `Run request failed with ${runResponse.status}`);
      }

      setResult(runPayload);
      setTraceIdInput(runPayload.traceId);

      const traceResponse = await fetch(
        `${normalizeApiBaseUrl(apiBaseUrl)}/agent/traces/${encodeURIComponent(runPayload.traceId)}`,
      );
      const tracePayload = await parseJson(traceResponse);
      if (!traceResponse.ok) {
        throw new Error(tracePayload?.detail || `Trace request failed with ${traceResponse.status}`);
      }

      setTrace(tracePayload);
    } catch (error) {
      setRunError(error.message);
      setTrace(EMPTY_TRACE);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLoadTrace = async (event) => {
    event.preventDefault();

    if (!traceIdInput.trim()) {
      setTraceError("Please provide a trace ID.");
      return;
    }

    setTraceError("");

    try {
      const traceResponse = await fetch(
        `${normalizeApiBaseUrl(apiBaseUrl)}/agent/traces/${encodeURIComponent(traceIdInput)}`,
      );
      const tracePayload = await parseJson(traceResponse);
      if (!traceResponse.ok) {
        throw new Error(tracePayload?.detail || `Trace request failed with ${traceResponse.status}`);
      }

      setTrace(tracePayload);
    } catch (error) {
      setTraceError(error.message);
      setTrace(EMPTY_TRACE);
    }
  };

  const handleCopyTraceId = async () => {
    if (!result?.traceId) {
      return;
    }

    try {
      await navigator.clipboard.writeText(result.traceId);
      setCopyFeedback("Copied");
      window.setTimeout(() => setCopyFeedback(""), 1200);
    } catch {
      setCopyFeedback("Copy failed");
      window.setTimeout(() => setCopyFeedback(""), 1200);
    }
  };

  return (
    <div className="app-shell">
      <main className="simple-layout">
        <section className="panel">
          <h1>Finance Agent Task Runner</h1>

          <form className="run-form" onSubmit={handleSubmit}>
            <label className="field-label" htmlFor="user-request">
              User Request
            </label>
            <textarea
              id="user-request"
              className="textarea-input"
              rows="2"
              value={userRequest}
              onChange={(event) => setUserRequest(event.target.value)}
              placeholder="Please check invoice INV-1001"
            />

            <div className="inline-row">
              <button className="primary-button" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Running..." : "Run Agent"}
              </button>
            </div>
          </form>

          {runError ? (
            <div className="message-card message-card-error">
              <span className="message-title">Error</span>
              <p>{runError}</p>
            </div>
          ) : null}
        </section>

        <section className="panel">
          <h2>Final Answer</h2>
          <div className="result-header">
            <span className={getResultBadgeClassName(result?.status)}>
              {getResultBadgeLabel(result?.status)}
            </span>
          </div>
          <div className="answer-block">
            {renderAnswer(result?.finalAnswer || "Submit a request to see the final answer.")}
          </div>

          <h2>Actions</h2>
          {result?.actions?.length ? (
            <ul className="simple-list">
              {result.actions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          ) : (
            <p className="muted-copy">No actions yet.</p>
          )}

          <div className="meta-grid">
            <div>
              <span className="field-label">Status</span>
              <p>{result?.status ?? "-"}</p>
            </div>
            <div>
              <span className="field-label">Trace ID</span>
              <div className="trace-id-row">
                <p>{result?.traceId ?? "-"}</p>
                {result?.traceId ? (
                  <button className="copy-button" type="button" onClick={handleCopyTraceId}>
                    {copyFeedback || "Copy"}
                  </button>
                ) : null}
              </div>
            </div>
          </div>
        </section>

        <section className="panel">
          <h2>Execution Trace</h2>

          <form className="trace-form" onSubmit={handleLoadTrace}>
            <label className="field-label" htmlFor="trace-id-input">
              Trace ID
            </label>
            <div className="inline-row">
              <input
                id="trace-id-input"
                className="text-input"
                value={traceIdInput}
                onChange={(event) => setTraceIdInput(event.target.value)}
                placeholder="Paste a traceId"
                spellCheck="false"
              />
              <button className="secondary-button" type="submit">
                Load Trace
              </button>
            </div>
          </form>

          {traceError ? (
            <div className="message-card message-card-error">
              <span className="message-title">Trace Error</span>
              <p>{traceError}</p>
            </div>
          ) : null}

          <p className="trace-summary"><strong>User Input:</strong> {trace.userInput || "-"}</p>
          <p className="trace-summary"><strong>Final Answer:</strong> {trace.finalAnswer || "-"}</p>

          <div className="step-stack">
            {trace.steps?.length ? (
              trace.steps.map((step, index) => (
                <article className="step-card" key={step.stepId}>
                  <div className="step-card-header">
                    <h3 className="step-title">
                      Step {index + 1} · {step.toolName} · {step.status}
                    </h3>
                    <span className={getStepBadgeClassName(step.status)}>{step.status}</span>
                  </div>

                  <div className="step-json-grid">
                    <div>
                      <span className="step-json-label">Input</span>
                      <pre>{JSON.stringify(step.input, null, 2)}</pre>
                    </div>
                    <div>
                      <span className="step-json-label">Output</span>
                      <pre>{JSON.stringify(step.output, null, 2)}</pre>
                    </div>
                  </div>

                  <div className="step-meta-grid">
                    <div>
                      <span className="step-json-label">Started At</span>
                      <p className="meta-line">{step.startedAt || "-"}</p>
                    </div>
                    <div>
                      <span className="step-json-label">Duration</span>
                      <p className="meta-line">{formatDuration(step.durationMs)}</p>
                    </div>
                  </div>
                  {step.error ? (
                    <div className="step-error">
                      <span className="step-json-label">Error</span>
                      <p>{step.error}</p>
                    </div>
                  ) : null}
                </article>
              ))
            ) : (
              <article className="empty-state">
                <h3>No trace loaded</h3>
                <p>Run the agent or load a trace ID to inspect execution steps.</p>
              </article>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

function normalizeApiBaseUrl(url) {
  return url.trim().replace(/\/$/, "");
}

async function parseJson(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function getResultBadgeLabel(status) {
  if (status === "failed") {
    return "Error";
  }

  if (status === "needs_input") {
    return "Needs Input";
  }

  if (status === "completed") {
    return "Completed";
  }

  return "Pending";
}

function getResultBadgeClassName(status) {
  if (status === "failed") {
    return "status-banner status-banner-error";
  }

  if (status === "needs_input") {
    return "status-banner status-banner-warning";
  }

  if (status === "completed") {
    return "status-banner status-banner-success";
  }

  return "status-banner";
}

function getStepBadgeClassName(status) {
  if (status === "failed") {
    return "status-pill failed";
  }

  return "status-pill";
}

function formatDuration(durationMs) {
  if (typeof durationMs !== "number") {
    return "-";
  }

  return `${durationMs} ms`;
}

function renderAnswer(answer) {
  const segments = formatAnswerSegments(answer);

  return segments.map((segment, index) => (
    <p className="answer-text" key={`${segment}-${index}`}>
      {segment}
    </p>
  ));
}

function formatAnswerSegments(answer) {
  const normalized = answer.replace(/\s+/g, " ").trim();
  if (!normalized) {
    return ["-"];
  }

  return normalized
    .split(/(?<=\.)\s+/)
    .map((segment) => segment.trim())
    .filter(Boolean);
}
