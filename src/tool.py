import json
from typing import Callable

### 
# Wraps function callables in a Tool class
### 

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
        "parameters": {"properties": {}},
    }
    schema = {
        k: {"type": v.__name__} for k, v in fn.__annotations__.items() if k != "return"
    }
    fn_signature['parameters']['properties'] = schema
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
        properties = fn_sig['parameters']['properties']

        type_mapping = {
            'int': int,
            'str': str,
            'bool': bool,
            'float': float
        }

        for arg_name, arg_val in tool_call_schema['arguments'].items():
            expected_type = properties[arg_name].get('type')

            if not isinstance(arg_val, type_mapping[expected_type]):
                tool_call_schema['arguments'][arg_name] = type_mapping[expected_type](arg_val)

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