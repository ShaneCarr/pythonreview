
import copy
def pass_by_value(func):
    def wrapper(*args, **kwargs):
        copied_args = copy.deepcopy(args)
        copied_kwargs = copy.deepcopy(kwargs)
        ## my_function = wrapper (the function object)
        return func(*copied_args, **copied_kwargs)
    return wrapper
