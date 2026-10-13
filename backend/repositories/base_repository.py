"""基础 Repository 类，提供通用的数据访问方法"""
import json
import os
from typing import List, Optional, TypeVar, Generic, Callable
from datetime import datetime

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """基础 Repository 类，使用 JSON 文件存储"""
    
    def __init__(self, file_path: str, from_dict: Callable[[dict], T], to_dict: Callable[[T], dict]):
        """初始化 Repository
        
        Args:
            file_path: JSON 文件路径
            from_dict: 从字典创建对象的函数
            to_dict: 将对象转换为字典的函数
        """
        self.file_path = file_path
        self.from_dict = from_dict
        self.to_dict = to_dict
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """确保数据文件存在"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def _load_data(self) -> List[dict]:
        """从文件加载数据"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_data(self, data: List[dict]):
        """保存数据到文件"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def find_all(self) -> List[T]:
        """查询所有记录"""
        data = self._load_data()
        return [self.from_dict(item) for item in data]
    
    def find_by_id(self, id: str) -> Optional[T]:
        """根据 ID 查询记录"""
        data = self._load_data()
        for item in data:
            if item.get('id') == id:
                return self.from_dict(item)
        return None
    
    def save(self, entity: T) -> T:
        """保存记录"""
        data = self._load_data()
        entity_dict = self.to_dict(entity)
        
        # 检查是否已存在
        existing_index = None
        for i, item in enumerate(data):
            if item.get('id') == entity_dict.get('id'):
                existing_index = i
                break
        
        if existing_index is not None:
            # 更新现有记录
            data[existing_index] = entity_dict
        else:
            # 添加新记录
            data.append(entity_dict)
        
        self._save_data(data)
        return entity
    
    def update(self, entity: T) -> T:
        """更新记录"""
        return self.save(entity)
    
    def delete(self, id: str) -> None:
        """删除记录"""
        data = self._load_data()
        data = [item for item in data if item.get('id') != id]
        self._save_data(data)
    
    def find_by_field(self, field: str, value: any) -> List[T]:
        """根据字段值查询记录"""
        data = self._load_data()
        results = [item for item in data if item.get(field) == value]
        return [self.from_dict(item) for item in results]
    
    def count(self) -> int:
        """统计记录数量"""
        data = self._load_data()
        return len(data)
