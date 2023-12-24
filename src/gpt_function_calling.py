from contextvars import ContextVar
import json
import typing

import logger

log = logger.get("GPT_FUNCTION_CALLING")

class GptFunctionStore:
    available_tools = []
    tool_lookup = {}
    trigger_message = ContextVar("current_message")

    def register(self, func):
        schema = mk_tool_description(func)
        func.schema = schema
        self.available_tools.append(func)
        self.tool_lookup[schema["function"]["name"]] = func
        return func

    def get_trigger_message(self):
        return self.trigger_message.get()

    def get_functions_schema(self):
        return [t.schema for t in self.available_tools]


    async def handle_tool_call(self, message, tool_call):
        if tool_call["type"] != "function":
            return

        try:
            log.info("Handling tool call: %s", tool_call)
            func = self.tool_lookup[tool_call["function"]["name"]]
            arguments = json.loads(tool_call["function"]["arguments"])
            token = self.trigger_message.set(message)
            return {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "name": tool_call["function"]["name"],
                "content": await func(**arguments),
            }
        except Exception as e:
            log.error("Function call %s failed with exception %s", tool_call["function"]["name"], e)
            return {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "name": tool_call["function"]["name"],
                "content": f"Unexpected error when calling function {tool_call['function']['name']}"
            }
        finally:
            self.trigger_message.reset(token)

def mk_tool_description(func):
    def get_function_name(func): return func.__name__
    def get_function_description(func): return func.__doc__
    def get_function_parameters(func):
        def get_arg_description(hint):
            return hint.__metadata__[0]
        def get_arg_type(arg, hint):
            primary_type = typing.get_args(hint)[0]
            if primary_type == str:
                return "string"
            elif primary_type == int:
                return "integer"
            elif primary_type == float:
                return "number"
            elif primary_type == bool:
                return "boolean"
            else:
                raise Exception(f"Unsupported type {hint} for argument {arg}")

        parameters = {}
        for arg, hint in get_function_arguments(func):
            if hint is None:
                raise Exception(f"Missing type hint for argument {arg}")
            parameters[arg] = {"type": get_arg_type(arg, hint), "description": get_arg_description(hint)}
        return {
            "type": "object",
            "properties": parameters,
            "required": list(parameters.keys()),
        }

    return {
        "type": "function",
        "function": {
            "description": get_function_description(func),
            "name": get_function_name(func),
            "parameters": get_function_parameters(func),
        }
    }

def get_function_arguments(func):
    type_hints = typing.get_type_hints(func, include_extras=True)
    arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
    return [(arg, type_hints.get(arg, None)) for arg in arg_names]
