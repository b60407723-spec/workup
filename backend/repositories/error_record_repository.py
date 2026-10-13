"""错词记录 Repository"""
from typing import List, Optional
from datetime import datetime
from ..models import ErrorRecord
from .base_repository import BaseRepository


class ErrorRecordRepository:
    """错词记录数据访问层"""
    
    def __init__(self, file_path: str = 'data/error_records.json'):
        """初始化 ErrorRecordRepository
        
        Args:
            file_path: 数据文件路径
        """
        self.base_repo = BaseRepository(
            file_path=file_path,
            from_dict=self._from_dict,
            to_dict=self._to_dict
        )
    
    @staticmethod
    def _from_dict(data: dict) -> ErrorRecord:
        """从字典创建 ErrorRecord 对象"""
        return ErrorRecord(
            id=data['id'],
            user_id=data['user_id'],
            word_id=data['word_id'],
            wrong_answer=data['wrong_answer'],
            correct_answer=data['correct_answer'],
            timestamp=datetime.fromisoformat(data['timestamp']) if isinstance(data['timestamp'], str) else data['timestamp']
        )
    
    @staticmethod
    def _to_dict(record: ErrorRecord) -> dict:
        """将 ErrorRecord 对象转换为字典"""
        return {
            'id': record.id,
            'user_id': record.user_id,
            'word_id': record.word_id,
            'wrong_answer': record.wrong_answer,
            'correct_answer': record.correct_answer,
            'timestamp': record.timestamp.isoformat() if isinstance(record.timestamp, datetime) else record.timestamp
        }
    
    def find_all(self) -> List[ErrorRecord]:
        """查询所有错词记录"""
        return self.base_repo.find_all()
    
    def find_by_id(self, record_id: str) -> Optional[ErrorRecord]:
        """根据 ID 查询错词记录"""
        return self.base_repo.find_by_id(record_id)
    
    def save(self, record: ErrorRecord) -> ErrorRecord:
        """保存错词记录"""
        return self.base_repo.save(record)
    
    def delete(self, record_id: str) -> None:
        """删除错词记录"""
        self.base_repo.delete(record_id)
    
    def find_by_user(self, user_id: str) -> List[ErrorRecord]:
        """查询用户的错词记录"""
        return self.base_repo.find_by_field('user_id', user_id)
    
    def find_by_word(self, word_id: str) -> List[ErrorRecord]:
        """查询某个单词的错词记录"""
        return self.base_repo.find_by_field('word_id', word_id)
    
    def count_by_word(self, word_id: str, user_id: str) -> int:
        """统计某个单词的错误次数"""
        all_records = self.find_all()
        count = 0
        for record in all_records:
            if record.word_id == word_id and record.user_id == user_id:
                count += 1
        return count
    
    def find_by_user_and_word(self, user_id: str, word_id: str) -> List[ErrorRecord]:
        """查询用户对某个单词的错词记录"""
        all_records = self.find_all()
        return [r for r in all_records if r.user_id == user_id and r.word_id == word_id]
