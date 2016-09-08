from pyro import pyropi
import time

pyro = pyropi()
print pyro.box_id
pyro.fire_pin(0, 1)
pyro.fire_pin(1, 5)
pyro.fire_pin(0, 5)
