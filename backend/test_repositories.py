"""简单测试验证 Repository 实现"""
import os
import sys
from datetime import datetime
import uuid

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import Word, ErrorRecord, LearningRecord, TestSession
from backend.repositories import WordRepository, ErrorRecordRepository, LearningRecordRepository, TestSessionRepository


def test_word_repository():
    """测试 WordRepository"""
    print("测试 WordRepository...")
    
    # 使用临时文件
    repo = WordRepository('data/test_words.json')
    
    # 创建测试单词
    word = Word(
        id=str(uuid.uuid4()),
        word='hello',
        definition='你好',
        part_of_speech='noun',
        difficulty=1,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # 测试验证
    is_valid, error = word.validate()
    assert is_valid, f"单词验证失败: {error}"
    print("✓ 单词验证通过")
    
    # 测试保存
    saved_word = repo.save(word)
    assert saved_word.id == word.id
    print("✓ 单词保存成功")
    
    # 测试查询
    found_word = repo.find_by_id(word.id)
    assert found_word is not None
    assert found_word.word == 'hello'
    print("✓ 单词查询成功")
    
    # 测试更新
    found_word.definition = '您好'
    found_word.updated_at = datetime.now()
    repo.update(found_word)
    updated_word = repo.find_by_id(word.id)
    assert updated_word.definition == '您好'
    print("✓ 单词更新成功")
    
    # 测试删除
    repo.delete(word.id)
    deleted_word = repo.find_by_id(word.id)
    assert deleted_word is None
    print("✓ 单词删除成功")
    
    # 清理测试文件
    if os.path.exists('data/test_words.json'):
        os.remove('data/test_words.json')
    
    print("WordRepository 测试通过!\n")


def test_error_record_repository():
    """测试 ErrorRecordRepository"""
    print("测试 ErrorRecordRepository...")
    
    repo = ErrorRecordRepository('data/test_error_records.json')
    
    # 创建测试错词记录
    record = ErrorRecord(
        id=str(uuid.uuid4()),
        user_id='user1',
        word_id='word1',
        wrong_answer='helo',
        correct_answer='hello',
        timestamp=datetime.now()
    )
    
    # 测试验证
    is_valid, error = record.validate()
    assert is_valid, f"错词记录验证失败: {error}"
    print("✓ 错词记录验证通过")
    
    # 测试保存
    saved_record = repo.save(record)
    assert saved_record.id == record.id
    print("✓ 错词记录保存成功")
    
    # 测试查询
    found_record = repo.find_by_id(record.id)
    assert found_record is not None
    assert found_record.wrong_answer == 'helo'
    print("✓ 错词记录查询成功")
    
    # 测试按用户查询
    user_records = repo.find_by_user('user1')
    assert len(user_records) > 0
    print("✓ 按用户查询成功")
    
    # 清理测试文件
    if os.path.exists('data/test_error_records.json'):
        os.remove('data/test_error_records.json')
    
    print("ErrorRecordRepository 测试通过!\n")


def test_learning_record_repository():
    """测试 LearningRecordRepository"""
    print("测试 LearningRecordRepository...")
    
    repo = LearningRecordRepository('data/test_learning_records.json')
    
    # 创建测试学习记录
    record = LearningRecord(
        id=str(uuid.uuid4()),
        user_id='user1',
        word_id='word1',
        status='learning',
        last_review_time=datetime.now(),
        next_review_time=datetime.now(),
        review_count=0,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # 测试验证
    is_valid, error = record.validate()
    assert is_valid, f"学习记录验证失败: {error}"
    print("✓ 学习记录验证通过")
    
    # 测试保存
    saved_record = repo.save(record)
    assert saved_record.id == record.id
    print("✓ 学习记录保存成功")
    
    # 测试查询
    found_record = repo.find_by_id(record.id)
    assert found_record is not None
    assert found_record.status == 'learning'
    print("✓ 学习记录查询成功")
    
    # 清理测试文件
    if os.path.exists('data/test_learning_records.json'):
        os.remove('data/test_learning_records.json')
    
    print("LearningRecordRepository 测试通过!\n")


def test_test_session_repository():
    """测试 TestSessionRepository"""
    print("测试 TestSessionRepository...")
    
    repo = TestSessionRepository('data/test_sessions_test.json')
    
    # 创建测试会话
    session = TestSession(
        id=str(uuid.uuid4()),
        user_id='user1',
        word_ids=['word1', 'word2', 'word3'],
        start_time=datetime.now(),
        end_time=None,
        status='in_progress'
    )
    
    # 测试验证
    is_valid, error = session.validate()
    assert is_valid, f"测试会话验证失败: {error}"
    print("✓ 测试会话验证通过")
    
    # 测试保存
    saved_session = repo.save(session)
    assert saved_session.id == session.id
    print("✓ 测试会话保存成功")
    
    # 测试查询
    found_session = repo.find_by_id(session.id)
    assert found_session is not None
    assert found_session.status == 'in_progress'
    assert len(found_session.word_ids) == 3
    print("✓ 测试会话查询成功")
    
    # 清理测试文件
    if os.path.exists('data/test_sessions_test.json'):
        os.remove('data/test_sessions_test.json')
    
    print("TestSessionRepository 测试通过!\n")


if __name__ == '__main__':
    print("开始测试 Repository 层...\n")
    
    try:
        test_word_repository()
        test_error_record_repository()
        test_learning_record_repository()
        test_test_session_repository()
        
        print("=" * 50)
        print("所有测试通过! ✓")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
