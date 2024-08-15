
# from compas_3dec.threedec_config import ThreedecConfig
# from compas_3dec.model_3dec import Model_3dec

# model = Model_3dec()

# print(model.threedec_config.load_box([0,0,1], 0.001))
# print(model.threedec_config.load_along_direction([0,0,1],[0,0,0], 500))

# print(model.threedec_config.set_point_load([0,0,0], [0,0,-1], 500, 0.01))

# vec = 0.000141801,-4.47605e-09,0.000348811
vec = 0.0217209, 8.43998e-08, -0.00384262

from compas.geometry import norm_vector

nvec = norm_vector(vec)
print(nvec)
