import yaml
import os

class ConfigLoader:
    _instance = None
    _config = None
    _config_path = None  # 新增配置文件路径存储

    def __new__(cls, config_path="config.yaml"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config_path = config_path  # 保存路径到实例
            cls._instance.load_config(config_path)
        return cls._instance

    def load_config(self, config_path):
        """加载配置文件"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            raise Exception(f"配置文件 {config_path} 未找到")
        except Exception as e:
            raise Exception(f"加载配置文件失败: {str(e)}")

    def get(self, key_path, default=None):
        """获取配置值，支持多级路径，如 'llm.api_key'"""
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, key_path, value):
        """动态修改配置值"""
        keys = key_path.split('.')
        config_dict = self._config
        parent_dict = config_dict
        last_key = keys[-1]
        
        # 遍历键路径找到最后一级父节点
        for key in keys[:-1]:
            if isinstance(parent_dict, dict) and key in parent_dict:
                parent_dict = parent_dict[key]
        
        # 设置值
        parent_dict[last_key] = value
        
        # 写入配置文件
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            raise Exception(f"写入配置文件失败: {str(e)}")
            

# 全局配置实例
config = ConfigLoader()