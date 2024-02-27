from compas_model.interactions import Interaction


class Interaction3dec(Interaction):
    def __init__(self, name=None, type=None, normal=None, polygon=None, forces_per_vertex=None):
        # type: (str | None, str | None, Vector | list | None, Polygon | None, dict | None) -> None
        super().__init__(name)
        self.type = type
        self.normal = normal
        self.polygon = polygon
        self.forces_per_vertex = forces_per_vertex
