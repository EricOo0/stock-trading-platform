import sys
import os
# Add project root to path just in case
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from a2a.types import Task
    import inspect
    print(f"Task file: {inspect.getfile(Task)}")
    print(f"Task fields: {Task.model_fields.keys() if hasattr(Task, 'model_fields') else dir(Task)}")
except ImportError:
    print("Could not import a2a.types.Task")
except Exception as e:
    print(f"Error: {e}")
