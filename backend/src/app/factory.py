from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.planner import Planner
from app.agent.runner import AgentRunner
from app.agent.trace import TraceStore
from app.api.routes import create_router
from app.data.json_data_source import JsonDataSource
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.po_repository import PORepository
from app.repositories.policy_repository import PolicyRepository
from app.tools.invoice_lookup import InvoiceLookupTool
from app.tools.po_lookup import POLookupTool
from app.tools.policy_lookup import PolicyLookupTool
from app.tools.registry import ToolRegistry


class AppFactory:
    def create_app(self) -> FastAPI:
        load_dotenv()

        app = FastAPI(
            title="Finance Agent Task Runner",
            version="0.1.0",
        )
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://127.0.0.1:5173",
                "http://localhost:5173",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        data_dir = Path(__file__).parent / "data"
        data_source = JsonDataSource(data_dir=data_dir)

        invoice_repository = InvoiceRepository(data_source)
        po_repository = PORepository(data_source)
        policy_repository = PolicyRepository(data_source)

        invoice_lookup_tool = InvoiceLookupTool(invoice_repository)
        po_lookup_tool = POLookupTool(po_repository)
        policy_lookup_tool = PolicyLookupTool(policy_repository)

        tool_registry = ToolRegistry()
        tool_registry.register(invoice_lookup_tool)
        tool_registry.register(po_lookup_tool)
        tool_registry.register(policy_lookup_tool)

        planner = Planner()
        trace_store = TraceStore(directory=data_dir / "traces")

        agent_runner = AgentRunner(
            planner=planner,
            tool_registry=tool_registry,
            trace_store=trace_store,
        )

        router = create_router(agent_runner=agent_runner, trace_store=trace_store)
        app.include_router(router)

        return app
