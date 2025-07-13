from typing import List, Dict, Any
from dataclasses import dataclass
import copy

@dataclass
class Person:
    name: str
    age: int
    hobbies: List[str]
    metadata: Dict[str, Any]

original = Person(name="shane", age=18, hobbies=["python", "programming"], metadata={});

# test copy methods
print("reference copy")
reference_copy = original
reference_copy.name = "zoe"
print(original)

print("shallow copy")
shallow_copy = copy.copy(original)
print(shallow_copy)


print("deep copy")
deep_copy = copy.deepcopy(original)
deep_copy.name = "shane"
print("original {}".format(original))
print("deep_copy {}".format(deep_copy))

numbers = [1, 2, 3, 4, 5]
first, *middle, last = numbers
print(f"first: {first}")      # 1
print(f"middle: {middle}")    # [2, 3, 4]
print(f"last: {last}")        # 5


list1 = [1, 2, 3]
list2 = [4, 5, 6]

# Combine lists using unpacking
combined = [*list1, *list2]
print(combined)  # [1, 2, 3, 4, 5, 6]

# Add elements while unpacking
extended = [0, *list1, 99, *list2, 100]
print(extended)  # [0, 1, 2, 3, 99, 4, 5, 6, 100]

# Works with tuples too
tuple1 = (1, 2)
tuple2 = (3, 4)
combined_tuple = (*tuple1, *tuple2)
print(combined_tuple)  # (1, 2, 3, 4)

ict1 = {'a': 1, 'b': 2}
dict2 = {'c': 3, 'd': 4}

dict1 = {'a': 1, 'b': 2}
dict2 = {'c': 3, 'd': 4}

# Combine dictionaries using unpacking
combined = {**dict1, **dict2}
print(combined)  # {'a': 1, 'b': 2, 'c': 3, 'd': 4}

# Override values while unpacking
modified = {**dict1, 'b': 99, **dict2}
print(modified)  # {'a': 1, 'b': 99, 'c': 3, 'd': 4}

# Add new keys while unpacking
extended = {'start': 0, **dict1, 'middle': 50, **dict2, 'end': 100}
print(extended)  # {'start': 0, 'a': 1, 'b': 2, 'middle': 50, 'c': 3, 'd': 4, 'end': 100}

data = [10, 20, 30]

# *data doesn't have a "type" - it becomes the individual elements
# It's like writing: 10, 20, 30
# Merging configurations
default_config = {'timeout': 30, 'retries': 3, 'debug': False}
user_config = {'timeout': 60, 'debug': True}

final_config = {**default_config, **user_config}
# Result: {'timeout': 60, 'retries': 3, 'debug': True}

# Combining API responses
api_response_1 = [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
api_response_2 = [{'id': 3, 'name': 'Charlie'}]

all_users = [*api_response_1, *api_response_2]
# Result: [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}, {'id': 3, 'name': 'Charlie'}]

# Extracting parts of data
data = ['header', 'item1', 'item2', 'item3', 'footer']
header, *items, footer = data
print(f"Header: {header}")    # header
print(f"Items: {items}")      # ['item1', 'item2', 'item3']
print(f"Footer: {footer}")    # footer