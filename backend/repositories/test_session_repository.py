"""测试会话 Repository"""
from typing import List, Optional
from datetime import datetime
from ..models import TestSession
from .base_repository import BaseRepository


class TestSessionRepository:
    """测试会话数据访问层"""
    
    def __init__(self, file_path: str = 'data/test_sessions.json'):
        """初始化 TestSessionRepository
        
        Args:
            file_path: 数据文件路径
        """
        self.base_repo = BaseRepository(
            file_path=file_path,
            from_dict=self._from_dict,
            to_dict=self._to_dict
        )
    
    @staticmethod
    def _from_dict(data: dict) -> TestSession:
        """从字典创建 TestSession 对象"""
        return TestSession(
            id=data['id'],
            user_id=data['user_id'],
            word_ids=data['word_ids'],
            start_time=datetime.fromisoformat(data['start_time']) if isinstance(data['start_time'], str) else data['start_time'],
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') and isinstance(data['end_time'], str) else data.get('end_time'),
            status=data['status']
        )
    
    @staticmethod
    def _to_dict(session: TestSession) -> dict:
        """将 TestSession 对象转换为字典"""
        return {
            'id': session.id,
            'user_id': session.user_id,
            'word_ids': session.word_ids,
            'start_time': session.start_time.isoformat() if isinstance(session.start_time, datetime) else session.start_time,
            'end_time': session.end_time.isoformat() if session.end_time and isinstance(session.end_time, datetime) else session.end_time,
            'status': session.status
        }
    
    def find_all(self) -> List[TestSession]:
        """查询所有测试会话"""
        return self.base_repo.find_all()
    
    def find_by_id(self, session_id: str) -> Optional[TestSession]:
        """根据 ID 查询测试会话"""
        return self.base_repo.find_by_id(session_id)
    
    def save(self, session: TestSession) -> TestSession:
        """保存测试会话"""
        return self.base_repo.save(session)
    
    def update(self, session: TestSession) -> TestSession:
        """更新测试会话"""
        return self.base_repo.update(session)
    
    def delete(self, session_id: str) -> None:
        """删除测试会话"""
        self.base_repo.delete(session_id)
    
    def find_by_user(self, user_id: str) -> List[TestSession]:
        """查询用户的测试会话"""
        return self.base_repo.find_by_field('user_id', user_id)
    
    def find_by_status(self, user_id: str, status: str) -> List[TestSession]:
        """查询用户特定状态的测试会话"""
        all_sessions = self.find_by_user(user_id)
        return [s for s in all_sessions if s.status == status]
    
    def get_active_session(self, user_id: str) -> Optional[TestSession]:
        """获取用户当前进行中的测试会话"""
        active_sessions = self.find_by_status(user_id, 'in_progress')
        return active_sessions[0] if active_sessions else None
