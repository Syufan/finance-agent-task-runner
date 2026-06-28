Component / Layer Diagram
┌──────────────────────────────────────────────┐
│                 Application Startup           │
│                    main.py                    │
│     creates and connects all dependencies     │
└──────────────────────────────────────────────┘


┌──────────────── API / Presentation ────────────────┐
│ API Route                                           │
│ POST /agent/run                                     │
│ GET /agent/traces/{traceId}                         │
└───────────────────────┬────────────────────────────┘
                        │ calls
                        ▼
┌──────────────── Application / Use Case ────────────┐
│ AgentRunner                                         │
│  ├─ Planner                                         │
│  ├─ Context                                         │
│  └─ TraceStore                                      │
│                                                     │
│ ToolRegistry                                        │
└───────────────────────┬────────────────────────────┘
                        │ selects a tool
                        ▼
┌──────────────── Infrastructure ────────────────────┐
│ InvoiceLookupTool ──────► InvoiceRepository         │
│ POLookupTool ───────────► PORepository              │
│ PolicyLookupTool ───────► PolicyRepository          │
│                                                     │
│ Repositories ───────────► JSON files / DB / SAP API │
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
  │ decide next action: invoice_lookup
  ▼
ToolRegistry
  │ resolve selected tool
  ▼
Tool
  ▼
Repository
  ▼
JSON / Database
  │ result
  ▲
Tool
  ▲
AgentRunner
  │ update Context + Trace
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




