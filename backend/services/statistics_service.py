"""统计分析服务"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..repositories.word_repository import WordRepository
from ..repositories.learning_record_repository import LearningRecordRepository
from ..repositories.error_record_repository import ErrorRecordRepository
from ..repositories.test_session_repository import TestSessionRepository
from ..middleware.metrics import update_system_metrics


class StatisticsService:
    """统计分析业务逻辑"""
    
    def __init__(self):
        """初始化 StatisticsService"""
        self.word_repo = WordRepository()
        self.learning_repo = LearningRecordRepository()
        self.error_repo = ErrorRecordRepository()
        self.test_session_repo = TestSessionRepository()
    
    def refresh_system_metrics(self) -> None:
        """刷新系统级监控指标（单词总数、活跃用户数）
        
        活跃用户定义为在学习记录、错词记录或测试会话中出现过的去重用户数。
        在启动时以及写操作后调用。
        """
        total_words = len(self.word_repo.find_all())
        
        user_ids = set()
        user_ids.update(r.user_id for r in self.learning_repo.find_all())
        user_ids.update(r.user_id for r in self.error_repo.find_all())
        user_ids.update(s.user_id for s in self.test_session_repo.find_all())
        
        update_system_metrics(total_words, len(user_ids))
    
    def get_overall_stats(self, user_id: str) -> Dict:
        """获取总体统计数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            总体统计数据字典，包含：
            - total_words: 总学习单词数
            - mastered_count: 已掌握数量
            - learning_count: 学习中数量
            - unlearned_count: 未学习数量
            - test_count: 测试次数
            - average_accuracy: 平均正确率
        """
        # 获取所有单词
        all_words = self.word_repo.find_all()
        total_words_in_system = len(all_words)
        
        # 获取用户的学习记录
        learning_records = self.learning_repo.find_by_user(user_id)
        
        # 统计各状态的单词数
        mastered_count = len([r for r in learning_records if r.status == 'mastered'])
        learning_count = len([r for r in learning_records if r.status == 'learning'])
        reviewing_count = len([r for r in learning_records if r.status == 'reviewing'])
        
        # 总学习单词数 = 已掌握 + 学习中 + 复习中
        total_words = mastered_count + learning_count + reviewing_count
        
        # 未学习数量 = 系统中的单词总数 - 已学习的单词数
        unlearned_count = total_words_in_system - total_words
        
        # 获取测试会话统计
        test_sessions = self.test_session_repo.find_by_user(user_id)
        completed_sessions = [s for s in test_sessions if s.status == 'completed']
        test_count = len(completed_sessions)
        
        # 计算平均正确率
        average_accuracy = 0.0
        if test_count > 0:
            # 从错词记录和测试会话计算正确率
            total_questions = 0
            total_errors = 0
            
            for session in completed_sessions:
                total_questions += len(session.word_ids)
            
            # 统计这些会话中的错误数
            error_records = self.error_repo.find_by_user(user_id)
            
            # 计算每个会话的错误数
            for session in completed_sessions:
                session_errors = [e for e in error_records 
                                if e.word_id in session.word_ids 
                                and session.start_time <= e.timestamp <= (session.end_time or datetime.now())]
                total_errors += len(session_errors)
            
            if total_questions > 0:
                average_accuracy = (total_questions - total_errors) / total_questions
        
        return {
            'total_words': total_words,
            'mastered_count': mastered_count,
            'learning_count': learning_count,
            'reviewing_count': reviewing_count,
            'unlearned_count': unlearned_count,
            'test_count': test_count,
            'average_accuracy': round(average_accuracy, 4)
        }
    
    def get_difficulty_distribution(self, user_id: str) -> Dict:
        """获取难度分布统计
        
        Args:
            user_id: 用户ID
            
        Returns:
            难度分布数据，格式：
            {
                'difficulty_1': {'total': 10, 'mastered': 5, 'learning': 3, 'error_rate': 0.2},
                'difficulty_2': {...},
                ...
            }
        """
        # 获取用户的学习记录
        learning_records = self.learning_repo.find_by_user(user_id)
        
        # 获取所有单词
        all_words = self.word_repo.find_all()
        word_dict = {w.id: w for w in all_words}
        
        # 按难度分组统计
        difficulty_stats = {}
        
        for difficulty in range(1, 6):  # 难度 1-5
            # 获取该难度的所有单词
            difficulty_words = [w for w in all_words if w.difficulty == difficulty]
            total = len(difficulty_words)
            
            # 统计该难度下用户的学习情况
            difficulty_word_ids = {w.id for w in difficulty_words}
            
            mastered = len([r for r in learning_records 
                          if r.word_id in difficulty_word_ids and r.status == 'mastered'])
            learning = len([r for r in learning_records 
                          if r.word_id in difficulty_word_ids and r.status == 'learning'])
            reviewing = len([r for r in learning_records 
                           if r.word_id in difficulty_word_ids and r.status == 'reviewing'])
            
            # 计算错误率
            error_records = self.error_repo.find_by_user(user_id)
            difficulty_errors = [e for e in error_records if e.word_id in difficulty_word_ids]
            
            # 错误率 = 错误次数 / (已学习的单词数 * 假设每个单词平均测试次数)
            learned_count = mastered + learning + reviewing
            error_rate = 0.0
            if learned_count > 0:
                # 简化计算：错误率 = 唯一错词数 / 已学习单词数
                unique_error_words = len(set(e.word_id for e in difficulty_errors))
                error_rate = unique_error_words / learned_count if learned_count > 0 else 0.0
            
            difficulty_stats[f'difficulty_{difficulty}'] = {
                'total': total,
                'mastered': mastered,
                'learning': learning,
                'reviewing': reviewing,
                'error_rate': round(error_rate, 4)
            }
        
        return difficulty_stats
    
    def get_pos_analysis(self, user_id: str) -> Dict:
        """获取词性分析统计
        
        Args:
            user_id: 用户ID
            
        Returns:
            词性分布数据，格式：
            {
                'noun': {'total': 20, 'mastered': 10, 'learning': 5, 'error_count': 3},
                'verb': {...},
                ...
            }
        """
        # 获取用户的学习记录
        learning_records = self.learning_repo.find_by_user(user_id)
        
        # 获取所有单词
        all_words = self.word_repo.find_all()
        
        # 按词性分组统计
        pos_stats = {}
        
        # 获取所有词性类型
        all_pos = set(w.part_of_speech for w in all_words)
        
        for pos in all_pos:
            # 获取该词性的所有单词
            pos_words = [w for w in all_words if w.part_of_speech == pos]
            total = len(pos_words)
            
            # 统计该词性下用户的学习情况
            pos_word_ids = {w.id for w in pos_words}
            
            mastered = len([r for r in learning_records 
                          if r.word_id in pos_word_ids and r.status == 'mastered'])
            learning = len([r for r in learning_records 
                          if r.word_id in pos_word_ids and r.status == 'learning'])
            reviewing = len([r for r in learning_records 
                           if r.word_id in pos_word_ids and r.status == 'reviewing'])
            
            # 统计错误次数
            error_records = self.error_repo.find_by_user(user_id)
            pos_errors = [e for e in error_records if e.word_id in pos_word_ids]
            error_count = len(pos_errors)
            
            pos_stats[pos] = {
                'total': total,
                'mastered': mastered,
                'learning': learning,
                'reviewing': reviewing,
                'error_count': error_count
            }
        
        return pos_stats
    
    def get_time_trend(self, user_id: str, start_date: Optional[str] = None, 
                       end_date: Optional[str] = None, granularity: str = 'day') -> Dict:
        """获取时间趋势统计
        
        Args:
            user_id: 用户ID
            start_date: 开始日期 (ISO格式字符串)，默认为30天前
            end_date: 结束日期 (ISO格式字符串)，默认为今天
            granularity: 时间粒度 ('day' 或 'week')
            
        Returns:
            时间趋势数据，格式：
            {
                'dates': ['2024-01-01', '2024-01-02', ...],
                'learned_words': [5, 3, 7, ...],
                'test_count': [2, 1, 3, ...],
                'error_count': [3, 2, 5, ...]
            }
        """
        # 解析日期范围
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now()
        
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = end - timedelta(days=30)
        
        # 过滤时间范围内的数据
        learning_records = self._filter_by_time_range(
            self.learning_repo.find_by_user(user_id),
            start, end, 'created_at'
        )
        
        error_records = self._filter_by_time_range(
            self.error_repo.find_by_user(user_id),
            start, end, 'timestamp'
        )
        
        test_sessions = self._filter_by_time_range(
            [s for s in self.test_session_repo.find_by_user(user_id) if s.status == 'completed'],
            start, end, 'start_time'
        )
        
        # 按时间粒度聚合数据
        if granularity == 'week':
            time_buckets = self._create_weekly_buckets(start, end)
        else:  # day
            time_buckets = self._create_daily_buckets(start, end)
        
        # 初始化统计数据
        dates = []
        learned_words = []
        test_count = []
        error_count = []
        
        for bucket_start, bucket_end in time_buckets:
            # 格式化日期
            if granularity == 'week':
                date_label = bucket_start.strftime('%Y-W%W')
            else:
                date_label = bucket_start.strftime('%Y-%m-%d')
            
            dates.append(date_label)
            
            # 统计该时间段内的学习单词数
            bucket_learned = len([r for r in learning_records 
                                if bucket_start <= r.created_at < bucket_end])
            learned_words.append(bucket_learned)
            
            # 统计该时间段内的测试次数
            bucket_tests = len([s for s in test_sessions 
                              if bucket_start <= s.start_time < bucket_end])
            test_count.append(bucket_tests)
            
            # 统计该时间段内的错误次数
            bucket_errors = len([e for e in error_records 
                               if bucket_start <= e.timestamp < bucket_end])
            error_count.append(bucket_errors)
        
        return {
            'dates': dates,
            'learned_words': learned_words,
            'test_count': test_count,
            'error_count': error_count
        }
    
    def _filter_by_time_range(self, records: List, start: datetime, 
                             end: datetime, time_field: str) -> List:
        """按时间范围过滤记录
        
        Args:
            records: 记录列表
            start: 开始时间
            end: 结束时间
            time_field: 时间字段名
            
        Returns:
            过滤后的记录列表
        """
        filtered = []
        for record in records:
            record_time = getattr(record, time_field)
            if start <= record_time <= end:
                filtered.append(record)
        return filtered
    
    def _create_daily_buckets(self, start: datetime, end: datetime) -> List[tuple]:
        """创建按天的时间桶
        
        Args:
            start: 开始日期
            end: 结束日期
            
        Returns:
            时间桶列表，每个元素为 (bucket_start, bucket_end)
        """
        buckets = []
        current = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end_normalized = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        while current <= end_normalized:
            bucket_end = current + timedelta(days=1)
            buckets.append((current, bucket_end))
            current = bucket_end
        
        return buckets
    
    def _create_weekly_buckets(self, start: datetime, end: datetime) -> List[tuple]:
        """创建按周的时间桶
        
        Args:
            start: 开始日期
            end: 结束日期
            
        Returns:
            时间桶列表，每个元素为 (bucket_start, bucket_end)
        """
        buckets = []
        # 找到开始日期所在周的周一
        current = start - timedelta(days=start.weekday())
        current = current.replace(hour=0, minute=0, second=0, microsecond=0)
        end_normalized = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        while current <= end_normalized:
            bucket_end = current + timedelta(days=7)
            buckets.append((current, bucket_end))
            current = bucket_end
        
        return buckets
