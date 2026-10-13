from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class Word:
    """单词数据模型"""
    id: str
    word: str
    definition: str
    part_of_speech: str
    difficulty: int
    created_at: datetime
    updated_at: datetime
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """验证单词数据的有效性
        
        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        if not self.word or not self.word.strip():
            return False, "单词字段不能为空"
        
        if not self.definition or not self.definition.strip():
            return False, "释义字段不能为空"
        
        if not self.part_of_speech or not self.part_of_speech.strip():
            return False, "词性字段不能为空"
        
        valid_pos = ['noun', 'verb', 'adj', 'adv', 'prep', 'conj', 'pron', 'interj']
        if self.part_of_speech not in valid_pos:
            return False, f"词性必须是以下之一: {', '.join(valid_pos)}"
        
        if not isinstance(self.difficulty, int) or self.difficulty < 1 or self.difficulty > 5:
            return False, "难度等级必须是1-5之间的整数"
        
        return True, None
    
    @staticmethod
    def validate_input(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证输入数据的有效性（用于创建前验证）
        
        Args:
            data: 包含单词信息的字典
            
        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        required_fields = ['word', 'definition', 'part_of_speech']
        
        for field in required_fields:
            if field not in data or not data[field] or not str(data[field]).strip():
                return False, f"{field} 字段不能为空"
        
        if 'difficulty' in data:
            try:
                difficulty = int(data['difficulty'])
                if difficulty < 1 or difficulty > 5:
                    return False, "难度等级必须是1-5之间的整数"
            except (ValueError, TypeError):
                return False, "难度等级必须是整数"
        
        valid_pos = ['noun', 'verb', 'adj', 'adv', 'prep', 'conj', 'pron', 'interj']
        if data['part_of_speech'] not in valid_pos:
            return False, f"词性必须是以下之一: {', '.join(valid_pos)}"
        
        return True, None


@dataclass
class ErrorRecord:
    """错词记录数据模型"""
    id: str
    user_id: str
    word_id: str
    wrong_answer: str
    correct_answer: str
    timestamp: datetime
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """验证错词记录的有效性
        
        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        if not self.user_id or not self.user_id.strip():
            return False, "用户ID不能为空"
        
        if not self.word_id or not self.word_id.strip():
            return False, "单词ID不能为空"
        
        if not self.correct_answer or not self.correct_answer.strip():
            return False, "正确答案不能为空"
        
        # wrong_answer 可以为空字符串（用户未输入）
        if self.wrong_answer is None:
            return False, "错误答案字段不能为None"
        
        return True, None


@dataclass
class LearningRecord:
    """学习记录数据模型"""
    id: str
    user_id: str
    word_id: str
    status: str  # learning, mastered, reviewing
    last_review_time: datetime
    next_review_time: datetime
    review_count: int
    created_at: datetime
    updated_at: datetime
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """验证学习记录的有效性
        
        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        if not self.user_id or not self.user_id.strip():
            return False, "用户ID不能为空"
        
        if not self.word_id or not self.word_id.strip():
            return False, "单词ID不能为空"
        
        valid_statuses = ['learning', 'mastered', 'reviewing']
        if self.status not in valid_statuses:
            return False, f"状态必须是以下之一: {', '.join(valid_statuses)}"
        
        if not isinstance(self.review_count, int) or self.review_count < 0:
            return False, "复习次数必须是非负整数"
        
        return True, None


@dataclass
class TestSession:
    """测试会话数据模型"""
    id: str
    user_id: str
    word_ids: List[str]
    start_time: datetime
    end_time: Optional[datetime]
    status: str  # in_progress, completed
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """验证测试会话的有效性
        
        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        if not self.user_id or not self.user_id.strip():
            return False, "用户ID不能为空"
        
        if not self.word_ids or len(self.word_ids) == 0:
            return False, "测试单词列表不能为空"
        
        valid_statuses = ['in_progress', 'completed']
        if self.status not in valid_statuses:
            return False, f"状态必须是以下之一: {', '.join(valid_statuses)}"
        
        if self.end_time and self.end_time < self.start_time:
            return False, "结束时间不能早于开始时间"
        
        return True, None


@dataclass
class TestResult:
    """测试结果数据模型"""
    session_id: str
    total_count: int
    correct_count: int
    wrong_count: int
    accuracy: float
    duration: int
    timestamp: datetime
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """验证测试结果的有效性
        
        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        if not self.session_id or not self.session_id.strip():
            return False, "会话ID不能为空"
        
        if not isinstance(self.total_count, int) or self.total_count < 0:
            return False, "总题数必须是非负整数"
        
        if not isinstance(self.correct_count, int) or self.correct_count < 0:
            return False, "正确数必须是非负整数"
        
        if not isinstance(self.wrong_count, int) or self.wrong_count < 0:
            return False, "错误数必须是非负整数"
        
        if self.correct_count + self.wrong_count != self.total_count:
            return False, "正确数 + 错误数必须等于总题数"
        
        if not isinstance(self.accuracy, (int, float)) or self.accuracy < 0 or self.accuracy > 1:
            return False, "正确率必须是0-1之间的数值"
        
        if not isinstance(self.duration, int) or self.duration < 0:
            return False, "用时必须是非负整数"
        
        return True, None


@dataclass
class MapReduceJob:
    """MapReduce 作业数据模型"""
    id: str
    user_id: str
    mode: str  # local, hadoop
    status: str  # running, completed, failed
    start_time: datetime
    end_time: Optional[datetime]
    input_count: int
    error: Optional[str]
    result: Optional[List[Dict[str, Any]]]
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """验证 MapReduce 作业的有效性
        
        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        if not self.id or not self.id.strip():
            return False, "作业ID不能为空"
        
        if not self.user_id or not self.user_id.strip():
            return False, "用户ID不能为空"
        
        valid_modes = ['local', 'hadoop']
        if self.mode not in valid_modes:
            return False, f"运行模式必须是以下之一: {', '.join(valid_modes)}"
        
        valid_statuses = ['running', 'completed', 'failed']
        if self.status not in valid_statuses:
            return False, f"状态必须是以下之一: {', '.join(valid_statuses)}"
        
        if not isinstance(self.input_count, int) or self.input_count < 0:
            return False, "输入记录数必须是非负整数"
        
        if self.end_time and self.end_time < self.start_time:
            return False, "结束时间不能早于开始时间"
        
        return True, None


@dataclass
class HighFrequencyWord:
    """高频错词数据模型"""
    word_id: str
    word: str
    error_count: int
    definition: str
    part_of_speech: str


@dataclass
class ImportResult:
    """导入结果数据模型"""
    success_count: int
    failed_count: int
    failed_lines: List[dict]
    total_lines: int
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """验证导入结果的有效性
        
        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        if not isinstance(self.success_count, int) or self.success_count < 0:
            return False, "成功数量必须是非负整数"
        
        if not isinstance(self.failed_count, int) or self.failed_count < 0:
            return False, "失败数量必须是非负整数"
        
        if not isinstance(self.total_lines, int) or self.total_lines < 0:
            return False, "总行数必须是非负整数"
        
        if self.success_count + self.failed_count != self.total_lines:
            return False, "成功数 + 失败数必须等于总行数"
        
        return True, None
