from dataclasses import dataclass

from app.agent.context import AgentContext
from app.agent.planner import Planner, ActionType, NextAction
from app.agent.trace import AgentTrace, TraceStore
from app.tools.registry import ToolRegistry

@dataclass
class AgentRunResult:
    status: str
    finalAnswer: str
    actions: list[str]
    traceId: str

class AgentRunner:
    def __init__(
        self, 
        planner: Planner, 
        tool_registry: ToolRegistry,
        trace_store: TraceStore
        ) -> None:
        self._planner = planner
        self._tool_registry = tool_registry
        self.trace_store = trace_store

    def run(self, user_request: str) -> AgentRunResult:
        context = AgentContext(userRequest=user_request)
        trace = AgentTrace(userRequest=user_request)

        while True:
            action = self._planner.decide(context)

            if action.type == ActionType.ASK_CLARIFICATION:
                # trace.finalAnswer = action.message
                # self._trace_store.save(trace)
                # return needs_input result
                pass
            
            elif action.type == ActionType.FINISH:
                # final_answer = self._build_final_answer(context)
                # trace.finalAnswer = final_answer
                # self._trace_store.save(trace)
                # return completed result
                pass

            elif action.type == ActionType.CALL_TOOL:
                tool = self._tool_registry.get(action.tool_name)
                # result = tool.execute(action.tool_input)
                # context.update_from_tool_result(...)
                # trace.append_step(...)
                continue
            
            else:
                raise RuntimeError(f"Unsupported action type: {action.type}")