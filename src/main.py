import machine, sys, time
import rom.app

try:
    app.start()
except Exception as e:
    print("Fatal error in main:")
    sys.print_exception(e)

time.sleep(3)
machine.reset()
