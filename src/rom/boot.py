# This file is executed on every boot (including wake-boot from deepsleep)
import esp, gc, uos, machine

esp.osdebug(None)
#uos.dupterm(None, 1) # disable REPL on UART(0)

# cpu freq = 160MHz
machine.freq(160000000)

# memory auto collect (<16KB)
gc.threshold(16384)
gc.collect()
