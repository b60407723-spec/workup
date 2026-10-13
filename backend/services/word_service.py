"""单词管理服务"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ..models import Word, ImportResult
from ..repositories.word_repository import WordRepository
from ..repositories.learning_record_repository import LearningRecordRepository


class WordService:
    """单词管理业务逻辑"""
    
    def __init__(self, 
                 word_repo: Optional[WordRepository] = None,
                 learning_record_repo: Optional[LearningRecordRepository] = None):
        """初始化 WordService
        
        Args:
            word_repo: 单词仓库实例
            learning_record_repo: 学习记录仓库实例
        """
        self.word_repo = word_repo or WordRepository()
        self.learning_record_repo = learning_record_repo or LearningRecordRepository()
    
    def get_words(self, filter_params: Optional[Dict[str, Any]] = None) -> List[Word]:
        """获取单词列表
        
        Args:
            filter_params: 过滤参数（可选），支持 difficulty, part_of_speech 等
            
        Returns:
            单词列表
        """
        if not filter_params:
            return self.word_repo.find_all()
        
        words = self.word_repo.find_all()
        
        # 按难度过滤
        if 'difficulty' in filter_params:
            difficulty = filter_params['difficulty']
            words = [w for w in words if w.difficulty == difficulty]
        
        # 按词性过滤
        if 'part_of_speech' in filter_params:
            pos = filter_params['part_of_speech']
            words = [w for w in words if w.part_of_speech == pos]
        
        return words
    
    def get_word_by_id(self, word_id: str) -> Optional[Word]:
        """获取单词详情
        
        Args:
            word_id: 单词ID
            
        Returns:
            单词对象，如果不存在返回 None
        """
        return self.word_repo.find_by_id(word_id)
    
    def add_word(self, word_data: Dict[str, Any]) -> tuple[Optional[Word], Optional[str]]:
        """添加新单词
        
        Args:
            word_data: 单词数据字典，包含 word, definition, part_of_speech, difficulty
            
        Returns:
            (word, error_message): 成功返回单词对象和 None，失败返回 None 和错误信息
        """
        # 验证输入数据
        is_valid, error_msg = Word.validate_input(word_data)
        if not is_valid:
            return None, error_msg
        
        # 检查单词是否已存在（不区分大小写）
        existing_word = self.word_repo.find_by_word(word_data['word'])
        if existing_word:
            return None, f"单词 '{word_data['word']}' 已存在"
        
        # 创建新单词
        now = datetime.now()
        word = Word(
            id=str(uuid.uuid4()),
            word=word_data['word'].strip(),
            definition=word_data['definition'].strip(),
            part_of_speech=word_data['part_of_speech'],
            difficulty=int(word_data.get('difficulty', 1)),
            created_at=now,
            updated_at=now
        )
        
        # 保存单词
        saved_word = self.word_repo.save(word)
        return saved_word, None
    
    def import_words_from_file(self, file_path: str) -> ImportResult:
        """从文件批量导入单词
        
        Args:
            file_path: TXT 文件路径
            
        Returns:
            导入结果对象
        """
        success_count = 0
        failed_count = 0
        failed_lines = []
        total_lines = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, start=1):
                    total_lines += 1
                    line = line.strip()
                    
                    # 跳过空行
                    if not line:
                        continue
                    
                    # 解析行：word\tdefinition\tpart_of_speech\tdifficulty
                    parts = line.split('\t')
                    
                    if len(parts) < 3:
                        failed_count += 1
                        failed_lines.append({
                            'line_number': line_num,
                            'content': line,
                            'error': '格式错误：至少需要3个字段（单词、释义、词性）'
                        })
                        continue
                    
                    word_data = {
                        'word': parts[0].strip(),
                        'definition': parts[1].strip(),
                        'part_of_speech': parts[2].strip(),
                        'difficulty': int(parts[3].strip()) if len(parts) > 3 else 1
                    }
                    
                    # 尝试添加单词
                    word, error = self.add_word(word_data)
                    if word:
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_lines.append({
                            'line_number': line_num,
                            'content': line,
                            'error': error
                        })
        
        except FileNotFoundError:
            return ImportResult(
                success_count=0,
                failed_count=0,
                failed_lines=[{'error': f'文件不存在: {file_path}'}],
                total_lines=0
            )
        except Exception as e:
            return ImportResult(
                success_count=success_count,
                failed_count=failed_count + (total_lines - success_count - failed_count),
                failed_lines=failed_lines + [{'error': f'读取文件时发生错误: {str(e)}'}],
                total_lines=total_lines
            )
        
        return ImportResult(
            success_count=success_count,
            failed_count=failed_count,
            failed_lines=failed_lines,
            total_lines=total_lines
        )
    
    def mark_as_mastered(self, word_id: str, user_id: str) -> tuple[bool, Optional[str]]:
        """标记单词为已掌握
        
        Args:
            word_id: 单词ID
            user_id: 用户ID
            
        Returns:
            (success, error_message): 成功返回 True 和 None，失败返回 False 和错误信息
        """
        # 检查单词是否存在
        word = self.word_repo.find_by_id(word_id)
        if not word:
            return False, f"单词不存在: {word_id}"
        
        # 查找或创建学习记录
        learning_record = self.learning_record_repo.find_by_user_and_word(user_id, word_id)
        
        if learning_record:
            # 更新现有记录
            learning_record.status = 'mastered'
            learning_record.updated_at = datetime.now()
            self.learning_record_repo.update(learning_record)
        else:
            # 创建新记录
            from ..models import LearningRecord
            now = datetime.now()
            learning_record = LearningRecord(
                id=str(uuid.uuid4()),
                user_id=user_id,
                word_id=word_id,
                status='mastered',
                last_review_time=now,
                next_review_time=now,
                review_count=0,
                created_at=now,
                updated_at=now
            )
            self.learning_record_repo.save(learning_record)
        
        return True, None
