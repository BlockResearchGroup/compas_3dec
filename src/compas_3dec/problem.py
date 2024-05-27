from compas.data import Data
import inspect
import os


class Problem(Data):
    def __new__(cls, backend, input, working_path=None):
        if backend == "3dec" and cls is Problem:
            from compas_3dec.problem3dec_old import Problem3dec
            return object.__new__(Problem3dec)
        return object.__new__(cls)

    def __init__(self, backend, input, working_path=None):
        self.backend = backend
        self.input = input
        self.working_path = working_path
        if not self.working_path:
            caller_frame = inspect.stack()[-1]
            caller_filename = caller_frame.filename
            self.working_path = os.path.dirname(os.path.abspath(caller_filename))


# Usage
# problem = Problem("3dec")
# print(isinstance(problem, Problem3DEC))  # True
