
import math
import os
from typing import Dict, Any, Protocol, Optional

class AgentTool(Protocol):
    name: str
    description: str

    def execute(self, input_str: str) -> str:
        ...

class CalculatorTool:
    name = "Calculator"
    description = "Useful for performing mathematical calculations. Input should be a mathematical expression (e.g., '2 + 2', 'sqrt(16)')."

    def execute(self, input_str: str) -> str:
        try:
            # Safe evaluation using limited scope
            allowed_names = {
                k: v for k, v in math.__dict__.items() if not k.startswith("__")
            }
            allowed_names.update({"abs": abs, "round": round, "min": min, "max": max})

            # Cleanup input
            expression = input_str.strip().replace('^', '**')

            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return str(result)
        except Exception as e:
            return f"Error calculating '{input_str}': {str(e)}"

class NotepadTool:
    name = "Notepad"
    description = "Useful for saving, reading, and appending notes to a persistent file. Input format: 'command|content'. Commands: 'write', 'append', 'read'. Example: 'write|Buy milk', 'read|', 'append| and eggs'."

    def __init__(self, user_id: str):
        self.file_path = f"./profiles/{user_id}_notes.txt"
        self._ensure_dir()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def execute(self, input_str: str) -> str:
        try:
            if "|" in input_str:
                command, content = input_str.split("|", 1)
            else:
                command = input_str.strip()
                content = ""

            command = command.lower().strip()

            if command == "write":
                with open(self.file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return "Successfully overwrote note."

            elif command == "append":
                with open(self.file_path, "a", encoding="utf-8") as f:
                    f.write("\n" + content)
                return "Successfully appended to note."

            elif command == "read":
                if not os.path.exists(self.file_path):
                    return "No notes found."
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return f.read()

            else:
                return f"Unknown command: '{command}'. Available: write, append, read."

        except Exception as e:
            return f"Notepad Error: {str(e)}"

class ToolRegistry:
    def __init__(self, user_id: str):
        self.tools: Dict[str, AgentTool] = {}
        self.register(CalculatorTool())
        self.register(NotepadTool(user_id))

    def register(self, tool: AgentTool):
        self.tools[tool.name.lower()] = tool

    def get_tool(self, name: str) -> Optional[AgentTool]:
        return self.tools.get(name.lower())

    def get_descriptions(self) -> str:
        return "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools.values()])
