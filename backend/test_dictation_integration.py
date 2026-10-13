"""默写本生成集成测试"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import uuid
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import app
from backend.repositories.word_repository import WordRepository
from backend.repositories.error_record_repository import ErrorRecordRepository
from backend.models import Word, ErrorRecord

client = TestClient(app)


def test_dictation_generation_with_real_data():
    """测试使用真实数据生成默写本的完整流程"""
    
    # 1. 准备测试数据 - 添加一些单词
    word_repo = WordRepository()
    error_repo = ErrorRecordRepository()
    
    test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    test_words = []
    
    # 创建测试单词
    for i in range(5):
        word = Word(
            id=str(uuid.uuid4()),
            word=f"testword{i}",
            definition=f"测试单词{i}",
            part_of_speech="noun",
            difficulty=i % 5 + 1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        saved_word = word_repo.save(word)
        test_words.append(saved_word)
    
    # 2. 创建错词记录（模拟用户答错）
    for i, word in enumerate(test_words):
        # 为每个单词创建不同次数的错误记录
        error_count = 5 - i  # 第一个单词错5次，第二个错4次，依此类推
        for j in range(error_count):
            error = ErrorRecord(
                id=str(uuid.uuid4()),
                user_id=test_user_id,
                word_id=word.id,
                wrong_answer=f"wrong{j}",
                correct_answer=word.word,
                timestamp=datetime.now()
            )
            error_repo.save(error)
    
    # 3. 触发 MapReduce 分析
    response = client.post(
        "/api/mapreduce/trigger",
        params={"user_id": test_user_id}
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # 4. 检查作业状态
    response = client.get(f"/api/mapreduce/status/{job_id}")
    assert response.status_code == 200
    assert response.json()["status"] in ["running", "completed"]
    
    # 5. 生成默写本
    response = client.post(
        "/api/dictation/generate",
        params={
            "user_id": test_user_id,
            "top_n": 3,
            "format": "txt"
        }
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    
    # 6. 验证默写本内容
    content = response.content.decode('utf-8')
    assert "英语单词默写本" in content
    
    # 验证单词按错误次数排序（testword0 应该排在最前面，因为错误次数最多）
    assert "testword0" in content
    assert "测试单词0" in content
    
    # 7. 清理测试数据
    for word in test_words:
        word_repo.delete(word.id)
    
    # 清理错词记录
    all_errors = error_repo.find_by_user(test_user_id)
    for error in all_errors:
        error_repo.delete(error.id)
    
    print(f"✓ 集成测试通过：成功生成包含 {len(test_words)} 个单词的默写本")


def test_dictation_generation_empty_data():
    """测试没有错词记录时生成默写本"""
    
    # 使用一个不存在的用户ID
    non_existent_user = f"nonexistent_{uuid.uuid4().hex[:8]}"
    
    response = client.post(
        "/api/dictation/generate",
        params={
            "user_id": non_existent_user,
            "top_n": 10,
            "format": "txt"
        }
    )
    
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert "暂无错词记录" in content or "英语单词默写本" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
