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
        self.available_tools.append(schema)
        self.tool_lookup[schema["function"]["name"]] = func
        return func

    def get_trigger_message(self):
        return self.trigger_message.get()

    def get_functions_schema(self):
        return self.available_tools


    async def handle_tool_call(self, message, tool_call):
        if tool_call["type"] != "function":
            return

        try:
            tool_call_id = tool_call["id"]
            function = tool_call["function"]
            function_name = function["name"]

            log.info("Received tool call for function %s", function_name)
            func = self.tool_lookup[function_name]
            args_object = json.loads(function["arguments"])
            log.info("Calling function %s with arguments %s", function_name, args_object)
            arg_values = [args_object.get(arg_name) for arg_name, _ in get_function_arguments(func)]
            token = self.trigger_message.set(message)
            response = await func(**args_object)
            return {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": function_name,
                "content": response,
            }
        except Exception as e:
            log.error("Function call %s failed with exception %s", function_name, e)
            return {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": function_name,
                "content": f"Unexpected error when calling function {function_name}"
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
