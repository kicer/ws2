import ujson
import uos


class Config:
    """通用配置类，用于保存各种系统配置项"""

    CONFIG_FILE = "/config.json"
    _instance = None
    _initialized = False

    def __new__(cls):
        """单一实例模式实现"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self, ssid=None, password=None, city=None, **kwargs):
        """初始化配置，只在第一次调用时执行"""
        if not self._initialized:
            self.config_data = {"ssid": ssid, "password": password, "city": city}
            # 添加其他可能的自定义配置项
            self.config_data.update(kwargs)
            self._initialized = True
            # 自动加载配置文件
            self.load()

    def write(self):
        """将配置写入JSON格式的配置文件"""
        if self.is_valid():
            # 只将非None的值保存到文件
            save_data = {k: v for k, v in self.config_data.items() if v is not None}

            with open(self.CONFIG_FILE, "w") as f:
                ujson.dump(save_data, f)
            print(f"Writing configuration to {self.CONFIG_FILE}")
            # 写入后重新加载配置
            return self.load()
        return False

    def load(self):
        """从配置文件加载配置"""
        try:
            with open(self.CONFIG_FILE, "r") as f:
                loaded_data = ujson.load(f)

            self.config_data.update(loaded_data)
            print(f"Loading configuration from {self.CONFIG_FILE}")

            # 如果核心配置不完整，可能需要清除文件
            if not self.is_valid():
                print("Configuration incomplete, clearing config file")
                self.remove()
        except (OSError, ValueError):
            pass

        return self

    def get(self, key, default=None):
        """获取配置项"""
        return self.config_data.get(key, default)

    def set(self, key, value):
        """设置配置项"""
        self.config_data[key] = value

    def remove(self):
        """删除配置文件并重置配置"""
        try:
            uos.remove(self.CONFIG_FILE)
        except OSError:
            pass

        # 保留默认的关键配置项
        self.config_data = {"ssid": None, "password": None, "city": None}

    def is_valid(self):
        """检查核心配置项是否有效"""
        ssid = self.config_data.get("ssid")
        password = self.config_data.get("password")
        # 确保SSID和密码都是字符串类型且不为空
        if not ssid:
            return False
        if not password:
            return False

        return True


# 全局配置实例
config = Config()
