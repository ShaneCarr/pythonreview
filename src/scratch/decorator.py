import copy


def my_decorator(func):
    def wrapper():
        print("before")
        result = func()
        print("after")
        return result
    return wrapper

@my_decorator
def say_hello():
    print("hello")

say_hello()


def pass_by_value(func):
    def wrapper(*args, **kwargs):
        print("pass by value")
        copied_args = copy.deepcopy(args)
        copied_kwargs = copy.deepcopy(kwargs)
        ## my_function = wrapper (the function object)
        return func(*copied_args, **copied_kwargs)
    return wrapper



@pass_by_value
def test_function(my_list):
    print(f"Inside function: {my_list}")
    my_list.append("modified")

# Test it
original_list = [1, 2, 3]
print(f"Original before call: {original_list}")
test_function(original_list)
print(f"Original after call: {original_list}")



