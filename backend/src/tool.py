import json
from typing import Callable, get_origin, get_args, Literal, Union

def get_fn_signature(fn: Callable) -> dict:
    '''
        Generates signature for a given function
        Args:
            fn (Callable): function to extract signature from
        Returns:
            dict: dictionary containing function name, description, and parameter types
    '''
    fn_signature: dict = {
        "name": fn.__name__,
        "description": fn.__doc__,
        "parameters": {},
    }

    for param, annot in fn.__annotations__.items():
        if param == 'return':
            continue

        origin = get_origin(annot)
        args = get_args(annot)

        if origin is Union:
            # Union types
            none_args = [arg for arg in args if arg is not type(None)]
            if len(none_args) == 1:
                origin = get_origin(none_args[0])
                args = get_args(none_args[0])
            else:
                continue
        if origin is Literal: 
            # Literal types
            fn_signature['parameters'][param] = {
                "type": "string",
                "enum": list(args)
            }
        elif origin is list and get_origin(args[0]) is Literal:
            # Literal[List] types
            fn_signature['parameters'][param] = {
                "type": "array",
                "items": {"type": "string", "enum": list(get_args(args[0]))}
            }
        elif isinstance(annot, type):
            # Any other type
            fn_signature['parameters'][param] = {
                "type": annot.__name__
            }
    return fn_signature

class Tool:
    """
        Represents a tool that wraps a callable and it's signature

        Args:
            name (str): name of the function (the tool)
            fn (Callable): function that the tool represents
            fn_signature (str): JSON string representation of function's signature
    """

    def __init__(self, name: str, fn: Callable, fn_signature: str):
        self.name = name
        self.fn = fn
        self.fn_signature = fn_signature

    def __str__(self):
        return self.fn_signature
    
    def validate_args(self, tool_call_schema):
        '''
            Validates / converts arguments in the schema provided to match expected types
            Args:
                tool_call_schema (dict): arguments that will be passed to the tool
            Returns:
                dict tool call dictionary with arguments converted to correct types
        '''
        fn_sig = json.loads(self.fn_signature)
        properties = fn_sig['parameters']
        args = tool_call_schema['arguments']

        type_mapping = {
            'int': int,
            'str': str,
            'bool': bool,
            'float': float,
        }

        for arg_name, arg_val in args.items():
            expected_type = properties.get(arg_name, {}).get('type')
            
            if expected_type in type_mapping:
                if not isinstance(arg_val, type_mapping[expected_type]):
                    args[arg_name] = type_mapping[expected_type](arg_val)
            elif expected_type == 'array':
                if not isinstance(arg_val, list):
                    args[arg_name] = [arg_val]
                
                item_schema = properties[arg_name].get('items')
                if item_schema.get('type') == 'string' and 'enum' in item_schema:
                    args[arg_name] = [str(item) for item in args[arg_name]]
        return tool_call_schema

    def __call__(self, **kwargs):
        '''
            Executes tool with provided arguments
            Args:
                **kwargs: keyword arguments passed to function
            Returns:
                result of the function call
        '''
        return self.fn(**kwargs)
    
def tool(fn: Callable):
    '''
        decorator that wraps a function into a Tool object
        Args:
            fn (Callable): function to be wrapped
        Returns:
            Tool: tool object containing function, name, and signature
    '''
    fn_sig = get_fn_signature(fn)
    return Tool(
        name=fn_sig.get("name"), 
        fn=fn, 
        fn_signature=json.dumps(fn_sig)
    )