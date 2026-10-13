"""统计服务功能测试（带测试数据）"""
import sys
import os
from datetime import datetime, timedelta
import uuid

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.statistics_service import StatisticsService
from backend.repositories.word_repository import WordRepository
from backend.repositories.learning_record_repository import LearningRecordRepository
from backend.repositories.error_record_repository import ErrorRecordRepository
from backend.repositories.test_session_repository import TestSessionRepository
from backend.models import Word, LearningRecord, ErrorRecord, TestSession


def setup_test_data():
    """设置测试数据"""
    word_repo = WordRepository('data/test_words_stats.json')
    learning_repo = LearningRecordRepository('data/test_learning_stats.json')
    error_repo = ErrorRecordRepository('data/test_errors_stats.json')
    session_repo = TestSessionRepository('data/test_sessions_stats.json')
    
    # 清空现有数据
    for repo in [word_repo, learning_repo, error_repo, session_repo]:
        data_file = repo.base_repo.file_path
        if os.path.exists(data_file):
            os.remove(data_file)
    
    # 创建测试单词
    words = []
    for i in range(10):
        word = Word(
            id=f'word_{i}',
            word=f'test_word_{i}',
            definition=f'测试单词{i}',
            part_of_speech=['noun', 'verb', 'adj'][i % 3],
            difficulty=(i % 5) + 1,
            created_at=datetime.now() - timedelta(days=10-i),
            updated_at=datetime.now()
        )
        words.append(word)
        word_repo.save(word)
    
    # 创建学习记录
    user_id = 'test_user_stats'
    for i in range(7):
        status = 'mastered' if i < 3 else ('learning' if i < 5 else 'reviewing')
        record = LearningRecord(
            id=f'learning_{i}',
            user_id=user_id,
            word_id=f'word_{i}',
            status=status,
            last_review_time=datetime.now() - timedelta(days=i),
            next_review_time=datetime.now() + timedelta(days=i+1),
            review_count=i,
            created_at=datetime.now() - timedelta(days=10-i),
            updated_at=datetime.now()
        )
        learning_repo.save(record)
    
    # 创建错词记录
    for i in range(5):
        error = ErrorRecord(
            id=f'error_{i}',
            user_id=user_id,
            word_id=f'word_{i}',
            wrong_answer=f'wrong_{i}',
            correct_answer=f'test_word_{i}',
            timestamp=datetime.now() - timedelta(days=i)
        )
        error_repo.save(error)
    
    # 创建测试会话
    for i in range(3):
        session = TestSession(
            id=f'session_{i}',
            user_id=user_id,
            word_ids=[f'word_{j}' for j in range(5)],
            start_time=datetime.now() - timedelta(days=i+1),
            end_time=datetime.now() - timedelta(days=i+1, hours=-1),
            status='completed'
        )
        session_repo.save(session)
    
    return user_id


def test_overall_stats():
    """测试总体统计"""
    print("\n测试总体统计...")
    
    user_id = setup_test_data()
    stats_service = StatisticsService()
    stats_service.word_repo = WordRepository('data/test_words_stats.json')
    stats_service.learning_repo = LearningRecordRepository('data/test_learning_stats.json')
    stats_service.error_repo = ErrorRecordRepository('data/test_errors_stats.json')
    stats_service.test_session_repo = TestSessionRepository('data/test_sessions_stats.json')
    
    result = stats_service.get_overall_stats(user_id)
    
    print(f"总体统计结果: {result}")
    
    # 验证统计数据
    assert result['total_words'] == 7, f"期望 total_words=7, 实际={result['total_words']}"
    assert result['mastered_count'] == 3, f"期望 mastered_count=3, 实际={result['mastered_count']}"
    assert result['learning_count'] == 2, f"期望 learning_count=2, 实际={result['learning_count']}"
    assert result['reviewing_count'] == 2, f"期望 reviewing_count=2, 实际={result['reviewing_count']}"
    assert result['unlearned_count'] == 3, f"期望 unlearned_count=3, 实际={result['unlearned_count']}"
    assert result['test_count'] == 3, f"期望 test_count=3, 实际={result['test_count']}"
    
    print("✓ 总体统计测试通过")


def test_difficulty_distribution():
    """测试难度分布"""
    print("\n测试难度分布...")
    
    user_id = setup_test_data()
    stats_service = StatisticsService()
    stats_service.word_repo = WordRepository('data/test_words_stats.json')
    stats_service.learning_repo = LearningRecordRepository('data/test_learning_stats.json')
    stats_service.error_repo = ErrorRecordRepository('data/test_errors_stats.json')
    
    result = stats_service.get_difficulty_distribution(user_id)
    
    print(f"难度分布结果: {result}")
    
    # 验证每个难度等级都有数据
    for i in range(1, 6):
        key = f'difficulty_{i}'
        assert key in result, f"缺少 {key}"
        assert 'total' in result[key]
        assert 'mastered' in result[key]
        assert 'learning' in result[key]
        assert 'reviewing' in result[key]
        assert 'error_rate' in result[key]
    
    print("✓ 难度分布测试通过")


def test_pos_analysis():
    """测试词性分析"""
    print("\n测试词性分析...")
    
    user_id = setup_test_data()
    stats_service = StatisticsService()
    stats_service.word_repo = WordRepository('data/test_words_stats.json')
    stats_service.learning_repo = LearningRecordRepository('data/test_learning_stats.json')
    stats_service.error_repo = ErrorRecordRepository('data/test_errors_stats.json')
    
    result = stats_service.get_pos_analysis(user_id)
    
    print(f"词性分析结果: {result}")
    
    # 验证词性数据
    assert len(result) > 0, "应该有词性数据"
    
    for pos, data in result.items():
        assert 'total' in data
        assert 'mastered' in data
        assert 'learning' in data
        assert 'reviewing' in data
        assert 'error_count' in data
    
    print("✓ 词性分析测试通过")


def test_time_trend():
    """测试时间趋势"""
    print("\n测试时间趋势...")
    
    user_id = setup_test_data()
    stats_service = StatisticsService()
    stats_service.word_repo = WordRepository('data/test_words_stats.json')
    stats_service.learning_repo = LearningRecordRepository('data/test_learning_stats.json')
    stats_service.error_repo = ErrorRecordRepository('data/test_errors_stats.json')
    stats_service.test_session_repo = TestSessionRepository('data/test_sessions_stats.json')
    
    # 测试按天统计
    result = stats_service.get_time_trend(user_id, granularity='day')
    
    print(f"时间趋势结果（按天）: dates数量={len(result['dates'])}")
    
    assert 'dates' in result
    assert 'learned_words' in result
    assert 'test_count' in result
    assert 'error_count' in result
    
    # 验证数组长度一致
    assert len(result['dates']) == len(result['learned_words'])
    assert len(result['dates']) == len(result['test_count'])
    assert len(result['dates']) == len(result['error_count'])
    
    # 测试按周统计
    result_week = stats_service.get_time_trend(user_id, granularity='week')
    print(f"时间趋势结果（按周）: dates数量={len(result_week['dates'])}")
    
    assert len(result_week['dates']) > 0
    
    print("✓ 时间趋势测试通过")


def test_time_range_filter():
    """测试时间范围过滤"""
    print("\n测试时间范围过滤...")
    
    user_id = setup_test_data()
    stats_service = StatisticsService()
    stats_service.word_repo = WordRepository('data/test_words_stats.json')
    stats_service.learning_repo = LearningRecordRepository('data/test_learning_stats.json')
    stats_service.error_repo = ErrorRecordRepository('data/test_errors_stats.json')
    stats_service.test_session_repo = TestSessionRepository('data/test_sessions_stats.json')
    
    # 测试指定日期范围
    start = (datetime.now() - timedelta(days=7)).isoformat()
    end = datetime.now().isoformat()
    
    result = stats_service.get_time_trend(user_id, start_date=start, end_date=end, granularity='day')
    
    print(f"指定日期范围结果: dates数量={len(result['dates'])}")
    
    assert len(result['dates']) <= 8, "日期数量应该在合理范围内"
    
    print("✓ 时间范围过滤测试通过")


def cleanup_test_data():
    """清理测试数据"""
    test_files = [
        'data/test_words_stats.json',
        'data/test_learning_stats.json',
        'data/test_errors_stats.json',
        'data/test_sessions_stats.json'
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)


if __name__ == "__main__":
    print("=" * 60)
    print("开始测试统计服务（带测试数据）")
    print("=" * 60)
    
    try:
        test_overall_stats()
        test_difficulty_distribution()
        test_pos_analysis()
        test_time_trend()
        test_time_range_filter()
        
        print("\n" + "=" * 60)
        print("所有测试通过！✓")
        print("=" * 60)
        
        # 清理测试数据
        cleanup_test_data()
        print("\n测试数据已清理")
        
    except AssertionError as e:
        print(f"\n测试失败: {e}")
        cleanup_test_data()
        sys.exit(1)
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
        cleanup_test_data()
        sys.exit(1)
