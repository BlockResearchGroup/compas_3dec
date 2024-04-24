from compas.data import Data
import inspect
import os

class Problem(Data):
    def __new__(cls, backend, model, working_path=None):
        if backend == "3dec" and cls is Problem:
            from compas_3dec.problem3dec import Problem3dec
            return object.__new__(Problem3dec)
        return object.__new__(cls, backend=backend, model=model, working_path=working_path)
    def __init__(self, backend, model, working_path=None):
        self.backend = backend
        self.model = model
        self.working_path = working_path
        if not self.working_path:
            caller_frame = inspect.stack()[-1]
            caller_filename = caller_frame.filename
            self.working_path = os.path.dirname(os.path.abspath(caller_filename))



# Usage
# problem = Problem("3dec")
# print(isinstance(problem, Problem3DEC))  # True
