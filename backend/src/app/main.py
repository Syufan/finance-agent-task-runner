
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import create_router
from app.agent.runner import AgentRunner
from app.agent.trace import TraceStore

def _build_webserver() -> FastAPI:
    load_dotenv()

    app = FastAPI(
        title="Finance Agent Task Runner",
        version="0.1.0",
    )

    trace_store = TraceStore()
    agent_runner = AgentRunner(trace_store=trace_store)
    
    router = create_router(agent_runner=agent_runner, trace_store=trace_store)

    app.include_router(router)

    return app

app = _build_webserver()

def main() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()