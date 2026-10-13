"""单词 Repository"""
from typing import List, Optional
from datetime import datetime
from ..models import Word
from .base_repository import BaseRepository


class WordRepository:
    """单词数据访问层"""
    
    def __init__(self, file_path: str = 'data/words.json'):
        """初始化 WordRepository
        
        Args:
            file_path: 数据文件路径
        """
        self.base_repo = BaseRepository(
            file_path=file_path,
            from_dict=self._from_dict,
            to_dict=self._to_dict
        )
    
    @staticmethod
    def _from_dict(data: dict) -> Word:
        """从字典创建 Word 对象"""
        return Word(
            id=data['id'],
            word=data['word'],
            definition=data['definition'],
            part_of_speech=data['part_of_speech'],
            difficulty=data['difficulty'],
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
            updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at']
        )
    
    @staticmethod
    def _to_dict(word: Word) -> dict:
        """将 Word 对象转换为字典"""
        return {
            'id': word.id,
            'word': word.word,
            'definition': word.definition,
            'part_of_speech': word.part_of_speech,
            'difficulty': word.difficulty,
            'created_at': word.created_at.isoformat() if isinstance(word.created_at, datetime) else word.created_at,
            'updated_at': word.updated_at.isoformat() if isinstance(word.updated_at, datetime) else word.updated_at
        }
    
    def find_all(self) -> List[Word]:
        """查询所有单词"""
        return self.base_repo.find_all()
    
    def find_by_id(self, word_id: str) -> Optional[Word]:
        """根据 ID 查询单词"""
        return self.base_repo.find_by_id(word_id)
    
    def save(self, word: Word) -> Word:
        """保存单词"""
        return self.base_repo.save(word)
    
    def update(self, word: Word) -> Word:
        """更新单词"""
        return self.base_repo.update(word)
    
    def delete(self, word_id: str) -> None:
        """删除单词"""
        self.base_repo.delete(word_id)
    
    def find_by_word(self, word: str) -> Optional[Word]:
        """根据单词文本查询（不区分大小写）"""
        all_words = self.find_all()
        word_lower = word.lower().strip()
        for w in all_words:
            if w.word.lower().strip() == word_lower:
                return w
        return None
    
    def find_by_difficulty(self, difficulty: int) -> List[Word]:
        """根据难度查询单词"""
        return self.base_repo.find_by_field('difficulty', difficulty)
    
    def find_by_part_of_speech(self, pos: str) -> List[Word]:
        """根据词性查询单词"""
        return self.base_repo.find_by_field('part_of_speech', pos)
    
    def count(self) -> int:
        """统计单词数量"""
        return self.base_repo.count()
