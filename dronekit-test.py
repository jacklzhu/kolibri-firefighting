# interactive
import code

from dronekit import connect

vehicle = connect('tcp:127.0.0.1:5760', wait_ready=True)

cmds = vehicle.commands
cmds.download()
cmds.wait_ready()



code.interact(local=locals())
