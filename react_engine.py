
import re
import asyncio
from typing import List, Dict, Any, Tuple
from datetime import datetime

from core_types import ResponseGeneratorProtocol, IntentVector, MemoryFragment
from tools import ToolRegistry

# --- REACT PROMPT ---
REACT_SYSTEM_PROMPT = """
You are Resonance, an Ultra-Intelligent AI Agent with access to real-time tools.

Instructions:
1. You must answer the user's request as best as you can.
2. You have access to the following tools:
{tool_descriptions}

3. Use the following format strictly:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

4. If you do not need a tool, just give the Final Answer directly.
5. Current Date/Time: {current_time}
6. User Profile Context: {user_profile_summary}
7. Relevant Memories: {memory_context}

Begin!
"""

class ReActEngine:
    """Manages the Reason-Act loop."""
    def __init__(self, response_generator: ResponseGeneratorProtocol, tool_registry: ToolRegistry):
        self.response_generator = response_generator # Using the existing generator wrapper to access LLM
        self.tools = tool_registry
        self.max_steps = 5

    async def run(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the ReAct loop."""

        # Prepare Context Variables
        user_profile = context.get("user_profile")
        profile_summary = "Unknown"
        if user_profile:
             interests = ", ".join(user_profile.interests) if user_profile.interests else "None"
             profile_summary = f"ID: {user_profile.user_id}, Interests: {interests}"

        retrieved_memories = context.get('retrieved_memories', [])
        memory_summary = "\n".join([f"- {m.content.get('query')} -> {m.content.get('response')}" for m in retrieved_memories]) if retrieved_memories else "None"

        tool_desc = self.tools.get_descriptions()
        tool_names = ", ".join(self.tools.tools.keys())

        # Construct Initial Prompt
        system_prompt = REACT_SYSTEM_PROMPT.format(
            tool_descriptions=tool_desc,
            tool_names=tool_names,
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_profile_summary=profile_summary,
            memory_context=memory_summary
        )

        history = f"Question: {query}\n"
        execution_trace = [] # List of {thought, action, result} for UI

        step = 0
        while step < self.max_steps:
            # 1. Call LLM
            # We bypass the 'generate_response' method slightly or repurpose it?
            # 'generate_response' in response_generator.py uses a fixed template.
            # We need raw access or we need to trick it.
            # Since 'ResponseGeneratorProtocol' is high level, let's assume we can modify it
            # OR we pass this big prompt as the 'query' if the generator is simple.
            # However, SmartResponseGenerator uses 'model.generate_content_async(prompt)'.
            # We can override the prompt generation inside SmartResponseGenerator OR
            # we can just use the underlying model if we had access.
            # For this architecture, let's assume we pass the FULL prompt as the 'query'
            # and tell the generator to just complete it, ignoring its internal template?
            # No, that's messy.

            # Better approach: We will modify `SmartResponseGenerator` to accept a raw `override_prompt` argument in context?
            # Or simpler: We use the `generate_response` method but we wrap the system prompt into the 'query'
            # and hope the internal template doesn't break it.
            # Actually, the internal template wraps the query.
            # Let's fix this by adding `run_raw(prompt)` to the generator or checking context.

            # Let's try to inject via context['system_instruction'] if we modify generator.
            # For now, let's construct the prompt and pass it.

            # HACK: We will instantiate a new raw generation call here using the generator's internal model if possible.
            # But `response_generator` is a Protocol.
            # Let's assume we update `response_generator.py` to support `generate_raw`.
            pass

            # ... waiting for implementation details in step 3 ...
            # For now, let's assume self.response_generator has a method `generate_raw(prompt)`
            # We will add this method in the next file edit.

            full_prompt = system_prompt + history
            print(f"🔄 ReAct Step {step+1}...")

            llm_output = await self.response_generator.generate_raw(full_prompt)

            # 2. Parse Output
            parsed = self._parse_output(llm_output)

            if parsed['final_answer']:
                return {
                    "text": parsed['final_answer'],
                    "thought": parsed['thought'], # The last thought
                    "trace": execution_trace
                }

            if parsed['action']:
                action_name = parsed['action']
                action_input = parsed['action_input']

                # UI Log
                execution_trace.append({
                    "step": step + 1,
                    "thought": parsed['thought'],
                    "action": action_name,
                    "input": action_input,
                    "status": "running"
                })

                # 3. Execute Tool
                tool = self.tools.get_tool(action_name)
                if tool:
                    observation = tool.execute(action_input)
                else:
                    observation = f"Error: Tool '{action_name}' not found."

                # Update UI Log
                execution_trace[-1]["observation"] = observation
                execution_trace[-1]["status"] = "complete"

                # 4. Append to History
                history += f"{llm_output}\nObservation: {observation}\n"
                step += 1
            else:
                # LLM failed to follow format, or just gave a thought without action/final answer?
                # We assume it's the final answer if no action found.
                return {
                    "text": llm_output,
                    "thought": parsed.get('thought'),
                    "trace": execution_trace
                }

        return {
            "text": "I timed out while thinking. Here is what I have so far.",
            "thought": "Max steps reached.",
            "trace": execution_trace
        }

    def _parse_output(self, text: str) -> Dict[str, Any]:
        """Parses the ReAct output."""
        result = {"thought": None, "action": None, "action_input": None, "final_answer": None}

        # Extract Thought
        thought_match = re.search(r"Thought:(.*?)(Action:|Final Answer:|$)", text, re.DOTALL)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()

        # Extract Final Answer
        final_match = re.search(r"Final Answer:(.*)", text, re.DOTALL)
        if final_match:
            result["final_answer"] = final_match.group(1).strip()
            return result

        # Extract Action
        action_match = re.search(r"Action:(.*?)\n", text)
        if action_match:
            result["action"] = action_match.group(1).strip()

        # Extract Action Input
        input_match = re.search(r"Action Input:(.*)", text, re.DOTALL)
        if input_match:
            result["action_input"] = input_match.group(1).strip()

        return result
