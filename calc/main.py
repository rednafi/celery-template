from random import randint

from calc.pkg_1 import chains as chains_1
from calc.pkg_2 import chains as chains_2

while True:
    res_1 = chains_1.add_sub(randint(1, 100), randint(101, 200))
    res_2 = chains_2.mul_div(randint(1000, 2000), randint(3000, 4000))
