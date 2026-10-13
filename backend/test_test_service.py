"""测试 TestService 功能"""
import os
import sys
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.test_service import TestService
from backend.repositories.word_repository import WordRepository
from backend.repositories.test_session_repository import TestSessionRepository
from backend.repositories.error_record_repository import ErrorRecordRepository
from backend.models import Word
import uuid


def setup_test_data():
    """设置测试数据"""
    word_repo = WordRepository('data/test_words_service.json')
    
    # 清空现有数据
    if os.path.exists('data/test_words_service.json'):
        os.remove('data/test_words_service.json')
    if os.path.exists('data/test_sessions_service.json'):
        os.remove('data/test_sessions_service.json')
    if os.path.exists('data/test_errors_service.json'):
        os.remove('data/test_errors_service.json')
    
    # 添加测试单词
    test_words = [
        Word(
            id=str(uuid.uuid4()),
            word="hello",
            definition="你好",
            part_of_speech="noun",
            difficulty=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Word(
            id=str(uuid.uuid4()),
            word="world",
            definition="世界",
            part_of_speech="noun",
            difficulty=2,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Word(
            id=str(uuid.uuid4()),
            word="test",
            definition="测试",
            part_of_speech="verb",
            difficulty=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    for word in test_words:
        word_repo.save(word)
    
    return word_repo


def test_start_test():
    """测试开始测试功能"""
    print("\n=== 测试开始测试功能 ===")
    
    word_repo = setup_test_data()
    test_service = TestService(
        test_session_repo=TestSessionRepository('data/test_sessions_service.json'),
        word_repo=word_repo,
        error_record_repo=ErrorRecordRepository('data/test_errors_service.json')
    )
    
    # 开始测试
    user_id = "test_user_1"
    session = test_service.start_test(user_id, 2)
    
    print(f"✓ 创建测试会话: {session.id}")
    print(f"  用户ID: {session.user_id}")
    print(f"  单词数量: {len(session.word_ids)}")
    print(f"  状态: {session.status}")
    
    assert session.user_id == user_id
    assert len(session.word_ids) == 2
    assert session.status == 'in_progress'
    
    return session


def test_submit_answer(session):
    """测试提交答案功能"""
    print("\n=== 测试提交答案功能 ===")
    
    word_repo = WordRepository('data/test_words_service.json')
    test_service = TestService(
        test_session_repo=TestSessionRepository('data/test_sessions_service.json'),
        word_repo=word_repo,
        error_record_repo=ErrorRecordRepository('data/test_errors_service.json')
    )
    
    # 获取第一个单词
    word_id = session.word_ids[0]
    word = word_repo.find_by_id(word_id)
    
    # 测试正确答案
    is_correct = test_service.submit_answer(session.id, word_id, word.word)
    print(f"✓ 提交正确答案: {word.word} -> {is_correct}")
    assert is_correct == True
    
    # 测试错误答案
    if len(session.word_ids) > 1:
        word_id_2 = session.word_ids[1]
        word_2 = word_repo.find_by_id(word_id_2)
        is_correct_2 = test_service.submit_answer(session.id, word_id_2, "wrong_answer")
        print(f"✓ 提交错误答案: wrong_answer (正确: {word_2.word}) -> {is_correct_2}")
        assert is_correct_2 == False
    
    # 测试大小写不敏感
    is_correct_case = test_service.submit_answer(session.id, word_id, word.word.upper())
    print(f"✓ 测试大小写不敏感: {word.word.upper()} -> {is_correct_case}")
    assert is_correct_case == True


def test_end_test(session):
    """测试结束测试功能"""
    print("\n=== 测试结束测试功能 ===")
    
    word_repo = WordRepository('data/test_words_service.json')
    test_service = TestService(
        test_session_repo=TestSessionRepository('data/test_sessions_service.json'),
        word_repo=word_repo,
        error_record_repo=ErrorRecordRepository('data/test_errors_service.json')
    )
    
    # 结束测试
    result = test_service.end_test(session.id)
    
    print(f"✓ 测试结果:")
    print(f"  总题数: {result.total_count}")
    print(f"  正确数: {result.correct_count}")
    print(f"  错误数: {result.wrong_count}")
    print(f"  正确率: {result.accuracy:.2%}")
    print(f"  用时: {result.duration}秒")
    
    assert result.total_count == len(session.word_ids)
    assert result.correct_count + result.wrong_count == result.total_count
    assert 0 <= result.accuracy <= 1
    
    # 验证会话已完成
    updated_session = test_service.get_test_session(session.id)
    assert updated_session.status == 'completed'
    print(f"✓ 会话状态已更新为: {updated_session.status}")


def test_record_error():
    """测试错词记录功能"""
    print("\n=== 测试错词记录功能 ===")
    
    word_repo = WordRepository('data/test_words_service.json')
    test_service = TestService(
        test_session_repo=TestSessionRepository('data/test_sessions_service.json'),
        word_repo=word_repo,
        error_record_repo=ErrorRecordRepository('data/test_errors_service.json')
    )
    
    # 获取一个单词
    words = word_repo.find_all()
    word = words[0]
    
    # 记录错词
    error_record = test_service.record_error(
        user_id="test_user_1",
        word_id=word.id,
        wrong_answer="wrong",
        correct_answer=word.word
    )
    
    print(f"✓ 记录错词:")
    print(f"  单词ID: {error_record.word_id}")
    print(f"  错误答案: {error_record.wrong_answer}")
    print(f"  正确答案: {error_record.correct_answer}")
    print(f"  时间戳: {error_record.timestamp}")
    
    assert error_record.user_id == "test_user_1"
    assert error_record.word_id == word.id
    assert error_record.wrong_answer == "wrong"
    assert error_record.correct_answer == word.word


def cleanup():
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")
    test_files = [
        'data/test_words_service.json',
        'data/test_sessions_service.json',
        'data/test_errors_service.json'
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"✓ 删除: {file}")


if __name__ == '__main__':
    try:
        print("开始测试 TestService...")
        
        # 测试开始测试
        session = test_start_test()
        
        # 测试提交答案
        test_submit_answer(session)
        
        # 测试结束测试
        test_end_test(session)
        
        # 测试错词记录
        test_record_error()
        
        print("\n" + "="*50)
        print("✓ 所有测试通过!")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup()
