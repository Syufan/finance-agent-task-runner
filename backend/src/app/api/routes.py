from fastapi import APIRouter, HTTPException

from app.agent.runner import AgentRunner
from app.agent.trace import TraceStore
from app.api.schemas import RunAgentRequest, RunAgentResponse, StepResponse, TraceResponse

def create_router(agent_runner: AgentRunner, trace_store: TraceStore) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health_check() -> dict:
        return {"status": "ok"}

    @router.post("/agent/run", response_model=RunAgentResponse)
    def run_agent(request: RunAgentRequest) -> RunAgentResponse:
        result = agent_runner.run(request.userRequest)
        return RunAgentResponse(
            status=result.status,
            finalAnswer=result.finalAnswer,
            actions=result.actions,
            traceId=result.traceId,
        )

    @router.get("/agent/traces/{trace_id}", response_model=TraceResponse)
    def get_trace(trace_id: str) -> TraceResponse:
        trace = trace_store.get(trace_id)

        if trace is None:
            raise HTTPException(
                status_code=404,
                detail="Trace not found",
            )

        return TraceResponse(
            traceId=trace.traceId,
            userInput=trace.userInput,
            steps=[
                StepResponse(
                    stepId=step.stepId,
                    stepName=step.stepName,
                    toolName=step.toolName,
                    input=step.input,
                    output=step.output,
                    status=step.status,
                    error=step.error,
                    startedAt=step.startedAt,
                    durationMs=step.durationMs,
                )
                for step in trace.steps
            ],
            finalAnswer=trace.finalAnswer,
        )
    return router