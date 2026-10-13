"""MapReduce 作业 Repository"""
from typing import List, Optional
from datetime import datetime
from ..models import MapReduceJob
from .base_repository import BaseRepository


class MapReduceJobRepository:
    """MapReduce 作业数据访问层"""
    
    def __init__(self, file_path: str = 'data/mapreduce_jobs.json'):
        """初始化 MapReduceJobRepository
        
        Args:
            file_path: 数据文件路径
        """
        self.base_repo = BaseRepository(
            file_path=file_path,
            from_dict=self._from_dict,
            to_dict=self._to_dict
        )
    
    @staticmethod
    def _from_dict(data: dict) -> MapReduceJob:
        """从字典创建 MapReduceJob 对象"""
        return MapReduceJob(
            id=data['id'],
            user_id=data['user_id'],
            mode=data['mode'],
            status=data['status'],
            start_time=datetime.fromisoformat(data['start_time']) if isinstance(data['start_time'], str) else data['start_time'],
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') and isinstance(data['end_time'], str) else data.get('end_time'),
            input_count=data.get('input_count', 0),
            error=data.get('error'),
            result=data.get('result')
        )
    
    @staticmethod
    def _to_dict(job: MapReduceJob) -> dict:
        """将 MapReduceJob 对象转换为字典"""
        return {
            'id': job.id,
            'user_id': job.user_id,
            'mode': job.mode,
            'status': job.status,
            'start_time': job.start_time.isoformat() if isinstance(job.start_time, datetime) else job.start_time,
            'end_time': job.end_time.isoformat() if job.end_time and isinstance(job.end_time, datetime) else job.end_time,
            'input_count': job.input_count,
            'error': job.error,
            'result': job.result
        }
    
    def find_all(self) -> List[MapReduceJob]:
        """查询所有作业"""
        return self.base_repo.find_all()
    
    def find_by_id(self, job_id: str) -> Optional[MapReduceJob]:
        """根据 ID 查询作业"""
        return self.base_repo.find_by_id(job_id)
    
    def save(self, job: MapReduceJob) -> MapReduceJob:
        """保存作业"""
        return self.base_repo.save(job)
    
    def update(self, job: MapReduceJob) -> MapReduceJob:
        """更新作业"""
        return self.base_repo.update(job)
    
    def delete(self, job_id: str) -> None:
        """删除作业"""
        self.base_repo.delete(job_id)
    
    def find_by_user(self, user_id: str) -> List[MapReduceJob]:
        """查询用户的作业"""
        return self.base_repo.find_by_field('user_id', user_id)
