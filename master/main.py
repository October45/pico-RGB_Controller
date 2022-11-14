#!/usr/bin/env python3
from server import runServer

try:
    runServer(8080)
except OSError as e:
    print(e)
    pass
