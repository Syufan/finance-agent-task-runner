Component / Layer Diagram
┌──────────────────────────────────────────────┐
│            Application Startup                │
│                 main.py                       │
│  Creates and wires application dependencies   │
└──────────────────────────────────────────────┘

┌──────────────── API / Presentation ────────────────┐
│ API Routes                                          │
│ POST /agent/run                                     │
│ GET /agent/traces/{traceId}                         │
└───────────────────────┬────────────────────────────┘
                        │ calls
                        ▼
┌────────────── Application / Use Case ──────────────┐
│ AgentRunner                                         │
│  ├─ Planner                                         │
│  ├─ ToolRegistry                                    │
│  └─ TraceStore                                      │
│                                                     │
│ Per-run objects:                                    │
│  ├─ AgentContext                                    │
│  └─ AgentTrace                                      │
└───────────────────────┬────────────────────────────┘
                        │ resolves and executes tools
                        ▼
┌────────────────── Tool Layer ──────────────────────┐
│ InvoiceLookupTool                                   │
│ POLookupTool                                        │
│ PolicyLookupTool                                    │
└───────────────────────┬────────────────────────────┘
                        │ queries
                        ▼
┌──────────────── Infrastructure / Data ─────────────┐
│ InvoiceRepository                                   │
│ PORepository                                        │
│ PolicyRepository                                    │
│                                                     │
│ JsonDataSource → JSON files                         │
│ Future option: Database / SAP API                   │
└─────────────────────────────────────────────────────┘





Sequence Diagram
User
  │ POST /agent/run
  ▼
API Route
  │ AgentRunner.run(userRequest)
  ▼
AgentRunner
  │ create Context
  │ create Trace
  ▼
Planner
  │ returns NextAction
  ▼
ToolRegistry
  │ resolve selected tool
  ▼
Tool
  ▼
Repository
  ▼
JSON files
  │ result
  ▲
Tool
  ▲
AgentRunner
  │ update Context + record Trace step
  ▼
Planner
  │ next action: po_lookup / policy_lookup / finish
  ▼
... repeat if needed ...
  │
  ▼
API Route
  │ finalAnswer + actions + traceId
  ▼
User





Planner decides.
Runner orchestrates.
Tools expose capabilities.
Repositories access data.
Context stores current run state.
Trace records execution history.




Architecture Explanation

Design Goal

The system models invoice resolution as a traceable multi-step agent workflow. A user request may require several dependent actions: looking up an invoice, checking its purchase order, retrieving a relevant policy, and returning a conclusion with a recommended next step.

Instead of hardcoding this flow inside an API route, the design separates planning, execution, data access, and observability. This keeps HTTP handling independent from workflow decisions, makes the decision logic testable, and allows tools or data sources to be replaced without changing the overall orchestration flow.

The central design principle is:

The system separates planning, tool execution, and trace recording instead of hardcoding business branches inside the API layer.

Planner and Runner Responsibilities

The Planner is responsible only for deciding the next workflow action from the current AgentContext. It does not execute tools or access repositories directly.

Its decisions are based on workflow state, including:

* whether an invoice ID is available;
* invoice, PO, and policy lookup states;
* retrieved invoice, purchase order, and policy data;
* invoice status, PO reference, and block reason;
* any error recorded during the current run.

For example, the planner may return one of three actions:

* ASK_CLARIFICATION when no invoice ID is provided;
* CALL_TOOL when more information is required;
* FINISH when the workflow has enough information, encounters a terminal error, or returns a partial answer.

The AgentRunner is the workflow orchestrator. It creates an AgentContext and AgentTrace for each request, repeatedly calls Planner.decide(context), resolves tools through the ToolRegistry, executes them, applies results back to the context, and records every step in the trace.

When the planner returns ASK_CLARIFICATION or FINISH, the runner builds the final API response and stores the completed trace in TraceStore.

Tool Registry and Tool Layer

The ToolRegistry decouples workflow orchestration from concrete tool implementations.

The planner selects a capability by tool name, such as invoice_lookup, po_lookup, or policy_lookup. The runner resolves that name through the registry and executes the returned tool. The runner therefore does not need direct dependencies on individual lookup tool classes.

This design means that adding a new tool mainly requires:

1. implementing the tool;
2. registering it in the registry;
3. adding a planner decision branch only when the new capability is needed by the workflow.

The runner execution mechanism remains unchanged.

Context, Trace, and Error Handling

AgentContext stores the current business state required for subsequent planning decisions. It contains the extracted invoice ID, lookup states, retrieved invoice/PO/policy data, and any current structured error. Context is per-run state and is not intended to be an audit log.

AgentTrace records what happened during a run. It includes the user input, selected tools, tool inputs and outputs, step status, errors, timestamps, durations, final answer, and final status. Trace data supports debugging, review, and frontend display through the trace endpoint.

AgentError represents structured failures such as an invalid invoice ID, an invoice or PO not being found, or a tool execution failure. Errors can be recorded in the context and trace, then used by the planner and runner to end the workflow with an appropriate failed or partial response.

Error and Degradation Strategy

The workflow distinguishes user input issues, expected business outcomes, and execution failures.

* Missing invoice ID: the workflow returns needs_input with a clarification message. No tool is called.
* Invalid invoice ID: validation fails before the normal workflow starts. The response is marked as failed and no tool is called.
* Invoice or PO not found: the lookup result updates the relevant context state to NOT_FOUND; the planner ends the workflow with a clear failure outcome.
* Tool execution failure: the runner catches the exception, marks the corresponding lookup state as FAILED, stores an AgentError, and records a failed trace step.
* Policy lookup failure or policy not found: the workflow preserves available invoice and PO information and returns a partial answer explaining that policy information is unavailable or missing.

This distinction avoids treating every unexpected condition as the same kind of failure and preserves useful information whenever possible.

Current Trade-offs and Future Extension

The current implementation uses a rule-based planner because the workflow is finite, deterministic, and easy to test. JSON-backed repositories allow local execution without external infrastructure. An in-memory TraceStore is sufficient for trace retrieval and frontend demonstration.

These choices intentionally optimize for clarity, determinism, and testability.

The architecture supports future extensions with limited changes:

* Database integration: replace the JSON-backed repository implementation while preserving repository contracts.
* SAP or external API integration: update the relevant tool, repository, or integration client layer without changing the planner and runner workflow model.
* LLM-based planning: replace or extend the Planner implementation while retaining AgentContext, ToolRegistry, and AgentRunner orchestration.
* Additional capabilities: add a new tool, register it, and introduce planner logic only where the new capability is needed.

The overall orchestration model remains stable because planning, execution, data access, and trace recording are separated by responsibility.