from subprocess import call

__all__ = ["Solver", "run"]


class Solver:
    def __init__(self, executable_path='"C:\\Program Files\\Itasca\\3DEC700\\exe64\\3dec700_console.exe"'):
        self.gui = False
        self.executable_path = executable_path

    def run(self, project_path, sequence=[]):
        args = ["cd", project_path, "&&", self.executable_path] + sequence
        call(" ".join(args), shell=True)


import os
HERE = os.path.dirname(__file__)
if __name__ == "__main__":
    s = Solver()
    s.run(HERE,["Test_assembly_from_3dec.py"])
