# Uros Petrevski, Nodesign.net, WEIO

import time
from UnixSocketClient import UnixSocketClient

# here goes name of this script
# other name will not work
#
# It opens file (unix domain socket)
# That was precedently opened by server
c = UnixSocketClient('weio_main')

print("hello")


recnik = ["ja", "sam", "mali", "ali", "sam", "smarac"]
# I can send one object here directly
c.send(recnik)


for a in range(0,10) :
    print str(a) + "\n"
    
    # I can send integer object here directely
    c.send(a)
    time.sleep(0.1)


