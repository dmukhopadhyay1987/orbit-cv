# src/orbit_cv/middleware/todo_tracker.py
import logging
from typing import Any, Callable, Dict, List, Optional
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage, SystemMessage

logger = logging.getLogger("orbit_cv.middleware.todo_tracker")


class TodoTrackerMiddleware(AgentMiddleware):
    """Middleware to track task execution state, log subagent todo progress,

    and inject current task status into prompt context before model execution.
    """

    name: str = "todo_tracker"

    def _inject_todo_context(self, request: Any) -> Any:
        """Inspects request messages or state and appends active todo state to prompt context."""
        try:
            # Extract state or message history from request
            messages = getattr(request, "messages", [])
            state = getattr(request, "state", {})

            # Retrieve active todos / pending tasks from state or fallback
            pending_tasks: List[Dict[str, Any]] = state.get("pending_tasks", [])
            completed_tasks: List[Dict[str, Any]] = state.get("completed_tasks", [])

            if not pending_tasks and not completed_tasks:
                return request

            # Format a concise status block for the model
            status_summary = (
                "\n\n[SYSTEM TASK TRACKER]\n"
                f"Pending Tasks ({len(pending_tasks)}): {[t.get('task') for t in pending_tasks]}\n"
                f"Completed Tasks ({len(completed_tasks)}): {[t.get('task') for t in completed_tasks]}\n"
                "Ensure all pending tasks are processed or explicitly delegated."
            )

            # Prepend or append to existing system messages
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    msg.content = f"{msg.content}{status_summary}"
                    break

        except Exception as err:
            logger.warning(f"Failed to inject todo context in TodoTrackerMiddleware: {err}")

        return request

    def _process_response_tasks(self, response: Any) -> Any:
        """Inspects AI message output for tool calls related to task tracking or delegation."""
        try:
            message = getattr(response, "message", response)
            if isinstance(message, AIMessage) and hasattr(message, "tool_calls"):
                for tool_call in message.tool_calls:
                    name = tool_call.get("name")
                    args = tool_call.get("args", {})

                    if name in ("delegate_to_subagent", "add_todo", "update_todo"):
                        logger.info(f"[TodoTracker] Intercepted task action '{name}': {args}")

        except Exception as err:
            logger.warning(f"Error processing response tasks in TodoTrackerMiddleware: {err}")

        return response

    def wrap_model_call(self, request: Any, handler: Callable) -> Any:
        """Sync model call interceptor."""
        updated_request = self._inject_todo_context(request)
        response = handler(updated_request)
        return self._process_response_tasks(response)

    async def awrap_model_call(self, request: Any, handler: Callable) -> Any:
        """Async model call interceptor."""
        updated_request = self._inject_todo_context(request)
        response = await handler(updated_request)
        return self._process_response_tasks(response)