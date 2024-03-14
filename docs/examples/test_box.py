
from compas_3dec.threedec_config import ThreedecConfig
from compas_3dec.model_3dec import Model_3dec

model = Model_3dec()

print(model.threedec_config.load_box([0,0,1], 0.001))
print(model.threedec_config.load_along_direction([0,0,1],[0,0,0], 500))

print(model.threedec_config.set_point_load([0,0,0], [0,0,-1], 500, 0.01))
