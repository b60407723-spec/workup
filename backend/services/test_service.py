"""测试服务业务逻辑"""
import random
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from ..models import TestSession, TestResult, ErrorRecord, Word
from ..repositories.test_session_repository import TestSessionRepository
from ..repositories.word_repository import WordRepository
from ..repositories.error_record_repository import ErrorRecordRepository
from ..middleware.metrics import record_test_session, record_test_answer


class TestService:
    """测试服务类，处理单词测试相关的业务逻辑"""
    
    def __init__(
        self,
        test_session_repo: Optional[TestSessionRepository] = None,
        word_repo: Optional[WordRepository] = None,
        error_record_repo: Optional[ErrorRecordRepository] = None
    ):
        """初始化 TestService
        
        Args:
            test_session_repo: 测试会话仓库
            word_repo: 单词仓库
            error_record_repo: 错词记录仓库
        """
        self.test_session_repo = test_session_repo or TestSessionRepository()
        self.word_repo = word_repo or WordRepository()
        self.error_record_repo = error_record_repo or ErrorRecordRepository()
    
    def start_test(self, user_id: str, word_count: int) -> TestSession:
        """开始测试会话
        
        根据需求 2.1：随机选择单词并创建测试会话
        
        Args:
            user_id: 用户 ID
            word_count: 测试单词数量
            
        Returns:
            TestSession: 创建的测试会话
            
        Raises:
            ValueError: 如果参数无效
        """
        if not user_id or not user_id.strip():
            raise ValueError("用户ID不能为空")
        
        if word_count <= 0:
            raise ValueError("测试单词数量必须大于0")
        
        # 检查是否已有进行中的测试，如果有则自动结束它
        active_session = self.test_session_repo.get_active_session(user_id)
        if active_session:
            # 自动结束之前未完成的会话
            active_session.end_time = datetime.now()
            active_session.status = 'cancelled'
            self.test_session_repo.update(active_session)
            record_test_session('cancelled')
        
        # 获取所有单词
        all_words = self.word_repo.find_all()
        if not all_words:
            raise ValueError("没有可用的单词进行测试")
        
        # 随机选择单词（如果单词总数少于请求数量，则使用所有单词）
        actual_count = min(word_count, len(all_words))
        selected_words = random.sample(all_words, actual_count)
        word_ids = [word.id for word in selected_words]
        
        # 创建测试会话
        session = TestSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            word_ids=word_ids,
            start_time=datetime.now(),
            end_time=None,
            status='in_progress'
        )
        
        # 验证并保存
        is_valid, error_msg = session.validate()
        if not is_valid:
            raise ValueError(f"测试会话数据无效: {error_msg}")
        
        return self.test_session_repo.save(session)
    
    def submit_answer(self, session_id: str, word_id: str, user_answer: str) -> bool:
        """提交答案并验证
        
        根据需求 2.2：验证答案正确性并提供即时反馈
        
        Args:
            session_id: 测试会话 ID
            word_id: 单词 ID
            user_answer: 用户答案
            
        Returns:
            bool: 答案是否正确
            
        Raises:
            ValueError: 如果会话不存在或单词不在测试中
        """
        # 获取测试会话
        session = self.test_session_repo.find_by_id(session_id)
        if not session:
            raise ValueError("测试会话不存在")
        
        if session.status != 'in_progress':
            raise ValueError("测试会话已结束")
        
        # 验证单词是否在测试中
        if word_id not in session.word_ids:
            raise ValueError("该单词不在当前测试中")
        
        # 获取单词
        word = self.word_repo.find_by_id(word_id)
        if not word:
            raise ValueError("单词不存在")
        
        # 验证答案（忽略大小写和首尾空格）
        is_correct = self._validate_answer(word.word, user_answer)
        record_test_answer(is_correct)
        
        # 如果答案错误，记录错词
        if not is_correct:
            self.record_error(session.user_id, word_id, user_answer, word.word)
        
        return is_correct
    
    def _validate_answer(self, correct_word: str, user_answer: str) -> bool:
        """验证答案正确性
        
        根据属性 6：答案验证正确性
        忽略大小写和首尾空格进行比较
        
        Args:
            correct_word: 正确答案
            user_answer: 用户答案
            
        Returns:
            bool: 答案是否正确
        """
        if user_answer is None:
            return False
        
        normalized_correct = correct_word.strip().lower()
        normalized_answer = user_answer.strip().lower()
        
        return normalized_correct == normalized_answer
    
    def record_error(self, user_id: str, word_id: str, wrong_answer: str, correct_answer: str) -> ErrorRecord:
        """记录错词
        
        根据需求 2.3：记录错词信息，包括单词、错误答案、正确答案和时间戳
        
        Args:
            user_id: 用户 ID
            word_id: 单词 ID
            wrong_answer: 错误答案
            correct_answer: 正确答案
            
        Returns:
            ErrorRecord: 创建的错词记录
            
        Raises:
            ValueError: 如果数据无效
        """
        # 创建错词记录
        error_record = ErrorRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            word_id=word_id,
            wrong_answer=wrong_answer if wrong_answer is not None else "",
            correct_answer=correct_answer,
            timestamp=datetime.now()
        )
        
        # 验证并保存
        is_valid, error_msg = error_record.validate()
        if not is_valid:
            raise ValueError(f"错词记录数据无效: {error_msg}")
        
        return self.error_record_repo.save(error_record)
    
    def end_test(self, session_id: str) -> TestResult:
        """结束测试并返回结果
        
        根据需求 2.4：显示测试结果统计，包括正确率、错误数量和用时
        
        Args:
            session_id: 测试会话 ID
            
        Returns:
            TestResult: 测试结果
            
        Raises:
            ValueError: 如果会话不存在或已结束
        """
        # 获取测试会话
        session = self.test_session_repo.find_by_id(session_id)
        if not session:
            raise ValueError("测试会话不存在")
        
        if session.status == 'completed':
            raise ValueError("测试会话已结束")
        
        # 更新会话状态
        session.end_time = datetime.now()
        session.status = 'completed'
        self.test_session_repo.update(session)
        record_test_session('completed')
        
        # 计算测试结果
        return self._calculate_test_result(session)
    
    def _calculate_test_result(self, session: TestSession) -> TestResult:
        """计算测试结果统计
        
        根据属性 8：测试结果统计正确性
        正确率 = 正确数 / 总题数，且正确数 + 错误数 = 总题数
        
        Args:
            session: 测试会话
            
        Returns:
            TestResult: 测试结果
        """
        total_count = len(session.word_ids)
        
        # 统计错误数量（查询该会话期间的错词记录）
        # 注意：这里假设在会话期间记录的错词都属于该会话
        # 更精确的做法是在 ErrorRecord 中添加 session_id 字段
        error_records = self.error_record_repo.find_by_user(session.user_id)
        
        # 只统计该会话中单词的错误
        wrong_count = 0
        for record in error_records:
            if record.word_id in session.word_ids and record.timestamp >= session.start_time:
                if session.end_time is None or record.timestamp <= session.end_time:
                    wrong_count += 1
        
        correct_count = total_count - wrong_count
        
        # 计算正确率
        accuracy = correct_count / total_count if total_count > 0 else 0.0
        
        # 计算用时（秒）
        if session.end_time:
            duration = int((session.end_time - session.start_time).total_seconds())
        else:
            duration = 0
        
        # 创建测试结果
        result = TestResult(
            session_id=session.id,
            total_count=total_count,
            correct_count=correct_count,
            wrong_count=wrong_count,
            accuracy=accuracy,
            duration=duration,
            timestamp=session.end_time or datetime.now()
        )
        
        # 验证结果
        is_valid, error_msg = result.validate()
        if not is_valid:
            raise ValueError(f"测试结果数据无效: {error_msg}")
        
        return result
    
    def get_test_session(self, session_id: str) -> Optional[TestSession]:
        """获取测试会话
        
        Args:
            session_id: 测试会话 ID
            
        Returns:
            TestSession: 测试会话，如果不存在则返回 None
        """
        return self.test_session_repo.find_by_id(session_id)
    
    def get_session_words(self, session_id: str) -> List[Word]:
        """获取测试会话中的单词列表
        
        Args:
            session_id: 测试会话 ID
            
        Returns:
            List[Word]: 单词列表
            
        Raises:
            ValueError: 如果会话不存在
        """
        session = self.test_session_repo.find_by_id(session_id)
        if not session:
            raise ValueError("测试会话不存在")
        
        words = []
        for word_id in session.word_ids:
            word = self.word_repo.find_by_id(word_id)
            if word:
                words.append(word)
        
        return words
