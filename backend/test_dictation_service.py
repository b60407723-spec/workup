"""测试默写本生成服务"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.dictation_service import DictationService
from backend.services.mapreduce_service import MapReduceService
from backend.repositories.word_repository import WordRepository
from backend.repositories.error_record_repository import ErrorRecordRepository
from backend.models import Word, ErrorRecord
from datetime import datetime
import uuid


def test_dictation_service_initialization():
    """测试 DictationService 初始化"""
    service = DictationService()
    assert service is not None
    assert service.mapreduce_service is not None


def test_get_high_frequency_words():
    """测试获取高频错词"""
    service = DictationService()
    
    # 获取高频错词（可能为空）
    words = service._get_high_frequency_words("default", 10)
    assert isinstance(words, list)
    assert len(words) <= 10


def test_format_as_txt_empty():
    """测试格式化空列表为 TXT"""
    service = DictationService()
    result = service.format_as_txt([])
    
    assert isinstance(result, str)
    assert "暂无错词记录" in result


def test_format_as_txt_with_words():
    """测试格式化单词列表为 TXT"""
    service = DictationService()
    
    words = [
        {
            'word_id': '1',
            'word': 'hello',
            'definition': '你好',
            'part_of_speech': 'noun',
            'error_count': 5
        },
        {
            'word_id': '2',
            'word': 'world',
            'definition': '世界',
            'part_of_speech': 'noun',
            'error_count': 3
        }
    ]
    
    result = service.format_as_txt(words)
    
    assert isinstance(result, str)
    assert "英语单词默写本" in result
    assert "hello" in result
    assert "world" in result
    assert "你好" in result
    assert "世界" in result
    assert "错误次数: 5" in result
    assert "错误次数: 3" in result


def test_generate_dictation_book_txt():
    """测试生成 TXT 格式默写本"""
    service = DictationService()
    
    result = service.generate_dictation_book(
        user_id="default",
        top_n=10,
        format="txt"
    )
    
    assert isinstance(result, bytes)
    # 解码验证内容
    text = result.decode('utf-8')
    assert "英语单词默写本" in text or "暂无错词记录" in text


def test_generate_dictation_book_pdf():
    """测试生成 PDF 格式默写本（可能失败如果没有 reportlab）"""
    service = DictationService()
    
    result = service.generate_dictation_book(
        user_id="default",
        top_n=10,
        format="pdf"
    )
    
    assert isinstance(result, bytes)
    # PDF 应该以 %PDF 开头，或者是错误消息
    if result.startswith(b'%PDF'):
        # 成功生成 PDF
        assert True
    else:
        # 可能是错误消息（reportlab 未安装）
        text = result.decode('utf-8')
        assert "reportlab" in text or "错误" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
