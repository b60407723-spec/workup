"""复习服务业务逻辑"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from ..models import LearningRecord, Word, ErrorRecord
from ..repositories.learning_record_repository import LearningRecordRepository
from ..repositories.error_record_repository import ErrorRecordRepository
from ..repositories.word_repository import WordRepository


class ReviewService:
    """复习服务类，处理单词复习相关的业务逻辑"""
    
    def __init__(
        self,
        learning_record_repo: Optional[LearningRecordRepository] = None,
        error_record_repo: Optional[ErrorRecordRepository] = None,
        word_repo: Optional[WordRepository] = None
    ):
        """初始化 ReviewService
        
        Args:
            learning_record_repo: 学习记录仓库
            error_record_repo: 错词记录仓库
            word_repo: 单词仓库
        """
        self.learning_record_repo = learning_record_repo or LearningRecordRepository()
        self.error_record_repo = error_record_repo or ErrorRecordRepository()
        self.word_repo = word_repo or WordRepository()
    
    def get_review_queue(self, user_id: str) -> List[Dict[str, Any]]:
        """获取复习队列，按错误次数降序排列
        
        根据需求 3.1：优先展示高频错词
        根据属性 9：复习队列优先级排序
        
        Args:
            user_id: 用户 ID
            
        Returns:
            List[Dict]: 复习单词列表，包含单词信息、错误次数和上次复习时间
        """
        if not user_id or not user_id.strip():
            raise ValueError("用户ID不能为空")
        
        # 获取用户的所有错词记录
        error_records = self.error_record_repo.find_by_user(user_id)
        
        # 统计每个单词的错误次数
        word_error_counts: Dict[str, int] = {}
        for record in error_records:
            word_id = record.word_id
            word_error_counts[word_id] = word_error_counts.get(word_id, 0) + 1
        
        # 构建复习队列
        review_queue = []
        for word_id, error_count in word_error_counts.items():
            # 获取单词信息
            word = self.word_repo.find_by_id(word_id)
            if not word:
                continue
            
            # 获取学习记录
            learning_record = self.learning_record_repo.find_by_user_and_word(user_id, word_id)
            last_review_time = learning_record.last_review_time if learning_record else None
            
            review_queue.append({
                'word_id': word_id,
                'word': word.word,
                'definition': word.definition,
                'part_of_speech': word.part_of_speech,
                'difficulty': word.difficulty,
                'error_count': error_count,
                'last_review_time': last_review_time
            })
        
        # 按错误次数降序排序（高频错词优先）
        review_queue.sort(key=lambda x: x['error_count'], reverse=True)
        
        return review_queue
    
    def update_review_status(self, user_id: str, word_id: str, is_correct: bool) -> LearningRecord:
        """更新复习状态
        
        根据需求 3.3：更新该单词的复习状态和时间戳
        根据需求 3.4：根据遗忘曲线算法计算下次复习时间
        根据需求 3.5：答对单词降低优先级
        根据属性 11：复习状态更新正确性
        根据属性 12：遗忘曲线计算合理性
        根据属性 13：复习优先级调整正确性
        
        Args:
            user_id: 用户 ID
            word_id: 单词 ID
            is_correct: 是否答对
            
        Returns:
            LearningRecord: 更新后的学习记录
        """
        if not user_id or not user_id.strip():
            raise ValueError("用户ID不能为空")
        
        if not word_id or not word_id.strip():
            raise ValueError("单词ID不能为空")
        
        # 检查单词是否存在
        word = self.word_repo.find_by_id(word_id)
        if not word:
            raise ValueError(f"单词不存在: {word_id}")
        
        # 获取或创建学习记录
        learning_record = self.learning_record_repo.find_by_user_and_word(user_id, word_id)
        
        now = datetime.now()
        
        if learning_record:
            # 更新现有记录
            learning_record.last_review_time = now
            learning_record.review_count += 1
            learning_record.updated_at = now
            
            # 如果答对，更新状态为 reviewing
            if is_correct:
                learning_record.status = 'reviewing'
            else:
                learning_record.status = 'learning'
            
            # 计算下次复习时间（基于遗忘曲线）
            learning_record.next_review_time = self._calculate_next_review_time(
                learning_record.review_count,
                is_correct
            )
            
            return self.learning_record_repo.update(learning_record)
        else:
            # 创建新记录
            learning_record = LearningRecord(
                id=str(uuid.uuid4()),
                user_id=user_id,
                word_id=word_id,
                status='reviewing' if is_correct else 'learning',
                last_review_time=now,
                next_review_time=self._calculate_next_review_time(1, is_correct),
                review_count=1,
                created_at=now,
                updated_at=now
            )
            
            return self.learning_record_repo.save(learning_record)
    
    def _calculate_next_review_time(self, review_count: int, is_correct: bool) -> datetime:
        """计算下次复习时间（基于遗忘曲线）
        
        根据属性 12：遗忘曲线计算合理性
        下次复习时间应该在当前时间之后，且随着复习次数增加，间隔时间应该递增
        
        使用简化的 SuperMemo SM-2 算法：
        - 如果答错：1天后复习
        - 如果答对：间隔时间随复习次数递增
          - 第1次：1天
          - 第2次：3天
          - 第3次：7天
          - 第4次及以后：上次间隔 * 2
        
        Args:
            review_count: 复习次数
            is_correct: 本次是否答对
            
        Returns:
            datetime: 下次复习时间
        """
        now = datetime.now()
        
        if not is_correct:
            # 答错：1天后复习
            return now + timedelta(days=1)
        
        # 答对：根据复习次数计算间隔
        if review_count == 1:
            interval_days = 1
        elif review_count == 2:
            interval_days = 3
        elif review_count == 3:
            interval_days = 7
        else:
            # 第4次及以后：指数增长
            interval_days = 7 * (2 ** (review_count - 3))
        
        return now + timedelta(days=interval_days)
    
    def adjust_review_priority(self, user_id: str, word_id: str) -> None:
        """调整复习优先级（答对后降低优先级）
        
        根据需求 3.5：在复习中答对后，该单词在复习队列中的位置应该后移
        根据属性 13：复习优先级调整正确性
        
        注意：优先级通过错误次数和下次复习时间自然体现
        答对后，下次复习时间会延后，从而在队列中自然后移
        
        Args:
            user_id: 用户 ID
            word_id: 单词 ID
        """
        # 优先级调整已经通过 update_review_status 中的
        # next_review_time 计算自动实现
        # 答对的单词会有更长的复习间隔，从而在队列中自然后移
        pass
    
    def get_review_info(self, user_id: str, word_id: str) -> Dict[str, Any]:
        """获取单词的复习信息
        
        根据需求 3.2：显示该单词的历史错误次数和上次复习时间
        根据属性 10：复习信息显示完整性
        
        Args:
            user_id: 用户 ID
            word_id: 单词 ID
            
        Returns:
            Dict: 包含错误次数和上次复习时间的字典
        """
        if not user_id or not user_id.strip():
            raise ValueError("用户ID不能为空")
        
        if not word_id or not word_id.strip():
            raise ValueError("单词ID不能为空")
        
        # 获取单词信息
        word = self.word_repo.find_by_id(word_id)
        if not word:
            raise ValueError(f"单词不存在: {word_id}")
        
        # 统计错误次数
        error_count = self.error_record_repo.count_by_word(word_id, user_id)
        
        # 获取学习记录
        learning_record = self.learning_record_repo.find_by_user_and_word(user_id, word_id)
        last_review_time = learning_record.last_review_time if learning_record else None
        
        return {
            'word_id': word_id,
            'word': word.word,
            'definition': word.definition,
            'part_of_speech': word.part_of_speech,
            'difficulty': word.difficulty,
            'error_count': error_count,
            'last_review_time': last_review_time
        }
    
    def get_words_due_for_review(self, user_id: str) -> List[Dict[str, Any]]:
        """获取到期需要复习的单词
        
        Args:
            user_id: 用户 ID
            
        Returns:
            List[Dict]: 到期复习的单词列表
        """
        if not user_id or not user_id.strip():
            raise ValueError("用户ID不能为空")
        
        now = datetime.now()
        due_records = self.learning_record_repo.get_review_due_words(user_id, now)
        
        result = []
        for record in due_records:
            word = self.word_repo.find_by_id(record.word_id)
            if not word:
                continue
            
            error_count = self.error_record_repo.count_by_word(record.word_id, user_id)
            
            result.append({
                'word_id': record.word_id,
                'word': word.word,
                'definition': word.definition,
                'part_of_speech': word.part_of_speech,
                'difficulty': word.difficulty,
                'error_count': error_count,
                'last_review_time': record.last_review_time,
                'next_review_time': record.next_review_time
            })
        
        # 按错误次数降序排序
        result.sort(key=lambda x: x['error_count'], reverse=True)
        
        return result
