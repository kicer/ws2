# WiFi天气微站

esp8266版天气信息显示设备


## API接口

1. /ping

2. /status

3. /weather
   /weather/?city=xxx&force=1

4. /lcd

5. /lcd/set, POST

6. /exec, POST

```sh
    # read memory free
    > *curl -H "Content-Type: application/json" -X POST -d '{"cmd":"import gc;gc.collect();R=gc.mem_free()", "token":"c6b74200"}' http://192.168.99.194/exec*

    # reset
    > *curl -H "Content-Type: application/json" -X POST -d '{"cmd":"import machine; machine.reset()", "token":"c6b74200"}' http://192.168.99.194/exec*


## 参考资料
[MicroPython remote control: mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html)
