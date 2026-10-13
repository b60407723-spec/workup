"""学习记录 Repository"""
from typing import List, Optional
from datetime import datetime
from ..models import LearningRecord
from .base_repository import BaseRepository


class LearningRecordRepository:
    """学习记录数据访问层"""
    
    def __init__(self, file_path: str = 'data/learning_records.json'):
        """初始化 LearningRecordRepository
        
        Args:
            file_path: 数据文件路径
        """
        self.base_repo = BaseRepository(
            file_path=file_path,
            from_dict=self._from_dict,
            to_dict=self._to_dict
        )
    
    @staticmethod
    def _from_dict(data: dict) -> LearningRecord:
        """从字典创建 LearningRecord 对象"""
        return LearningRecord(
            id=data['id'],
            user_id=data['user_id'],
            word_id=data['word_id'],
            status=data['status'],
            last_review_time=datetime.fromisoformat(data['last_review_time']) if isinstance(data['last_review_time'], str) else data['last_review_time'],
            next_review_time=datetime.fromisoformat(data['next_review_time']) if isinstance(data['next_review_time'], str) else data['next_review_time'],
            review_count=data['review_count'],
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
            updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at']
        )
    
    @staticmethod
    def _to_dict(record: LearningRecord) -> dict:
        """将 LearningRecord 对象转换为字典"""
        return {
            'id': record.id,
            'user_id': record.user_id,
            'word_id': record.word_id,
            'status': record.status,
            'last_review_time': record.last_review_time.isoformat() if isinstance(record.last_review_time, datetime) else record.last_review_time,
            'next_review_time': record.next_review_time.isoformat() if isinstance(record.next_review_time, datetime) else record.next_review_time,
            'review_count': record.review_count,
            'created_at': record.created_at.isoformat() if isinstance(record.created_at, datetime) else record.created_at,
            'updated_at': record.updated_at.isoformat() if isinstance(record.updated_at, datetime) else record.updated_at
        }
    
    def find_all(self) -> List[LearningRecord]:
        """查询所有学习记录"""
        return self.base_repo.find_all()
    
    def find_by_id(self, record_id: str) -> Optional[LearningRecord]:
        """根据 ID 查询学习记录"""
        return self.base_repo.find_by_id(record_id)
    
    def save(self, record: LearningRecord) -> LearningRecord:
        """保存学习记录"""
        return self.base_repo.save(record)
    
    def update(self, record: LearningRecord) -> LearningRecord:
        """更新学习记录"""
        return self.base_repo.update(record)
    
    def delete(self, record_id: str) -> None:
        """删除学习记录"""
        self.base_repo.delete(record_id)
    
    def find_by_user(self, user_id: str) -> List[LearningRecord]:
        """查询用户的学习记录"""
        return self.base_repo.find_by_field('user_id', user_id)
    
    def find_by_status(self, user_id: str, status: str) -> List[LearningRecord]:
        """查询用户特定状态的学习记录"""
        all_records = self.find_by_user(user_id)
        return [r for r in all_records if r.status == status]
    
    def get_mastered_words(self, user_id: str) -> List[str]:
        """获取已掌握的单词 ID 列表"""
        mastered_records = self.find_by_status(user_id, 'mastered')
        return [r.word_id for r in mastered_records]
    
    def find_by_user_and_word(self, user_id: str, word_id: str) -> Optional[LearningRecord]:
        """查询用户对某个单词的学习记录"""
        all_records = self.find_all()
        for record in all_records:
            if record.user_id == user_id and record.word_id == word_id:
                return record
        return None
    
    def get_review_due_words(self, user_id: str, current_time: datetime) -> List[LearningRecord]:
        """获取需要复习的单词"""
        all_records = self.find_by_user(user_id)
        return [r for r in all_records if r.next_review_time <= current_time and r.status != 'mastered']
