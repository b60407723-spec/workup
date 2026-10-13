"""MapReduce 集成测试"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.services.mapreduce_service import MapReduceService
from backend.repositories.error_record_repository import ErrorRecordRepository
from backend.repositories.word_repository import WordRepository
from backend.models import ErrorRecord, Word
from datetime import datetime
import uuid


def test_mapreduce_service():
    """测试 MapReduce 服务"""
    print("开始测试 MapReduce 服务...")
    
    # 初始化服务
    error_repo = ErrorRecordRepository('data/test_errors.json')
    word_repo = WordRepository('data/test_words.json')
    mapreduce_service = MapReduceService(error_repo, word_repo)
    
    # 清理测试数据
    test_error_file = Path('data/test_errors.json')
    test_word_file = Path('data/test_words.json')
    
    # 创建测试单词
    test_words = [
        Word(
            id='word1',
            word='hello',
            definition='你好',
            part_of_speech='noun',
            difficulty=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Word(
            id='word2',
            word='world',
            definition='世界',
            part_of_speech='noun',
            difficulty=2,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Word(
            id='word3',
            word='test',
            definition='测试',
            part_of_speech='verb',
            difficulty=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    for word in test_words:
        word_repo.save(word)
    
    # 创建测试错词记录
    test_errors = [
        ErrorRecord(
            id=str(uuid.uuid4()),
            user_id='test_user',
            word_id='word1',
            wrong_answer='helo',
            correct_answer='hello',
            timestamp=datetime.now()
        ),
        ErrorRecord(
            id=str(uuid.uuid4()),
            user_id='test_user',
            word_id='word1',
            wrong_answer='hallo',
            correct_answer='hello',
            timestamp=datetime.now()
        ),
        ErrorRecord(
            id=str(uuid.uuid4()),
            user_id='test_user',
            word_id='word2',
            wrong_answer='word',
            correct_answer='world',
            timestamp=datetime.now()
        ),
        ErrorRecord(
            id=str(uuid.uuid4()),
            user_id='test_user',
            word_id='word3',
            wrong_answer='tset',
            correct_answer='test',
            timestamp=datetime.now()
        ),
        ErrorRecord(
            id=str(uuid.uuid4()),
            user_id='test_user',
            word_id='word1',
            wrong_answer='helo',
            correct_answer='hello',
            timestamp=datetime.now()
        )
    ]
    
    for error in test_errors:
        error_repo.save(error)
    
    print(f"创建了 {len(test_words)} 个测试单词")
    print(f"创建了 {len(test_errors)} 个测试错词记录")
    
    # 测试触发分析
    print("\n触发 MapReduce 分析...")
    job_id = mapreduce_service.trigger_analysis('test_user')
    print(f"作业ID: {job_id}")
    
    # 测试获取作业状态
    print("\n获取作业状态...")
    status = mapreduce_service.get_job_status(job_id)
    print(f"状态: {status['status']}")
    
    if status['status'] == 'completed':
        print("✓ MapReduce 分析成功完成")
        
        # 测试获取分析结果
        print("\n获取分析结果...")
        results = mapreduce_service.get_analysis_results('test_user', job_id)
        
        print(f"\n高频错词列表 (共 {len(results)} 个):")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['word']} ({result['word_id']}) - 错误次数: {result['error_count']}")
            print(f"   释义: {result['definition']}")
            print(f"   词性: {result['part_of_speech']}")
        
        # 验证结果
        assert len(results) > 0, "应该有分析结果"
        assert results[0]['word_id'] == 'word1', "word1 应该是错误次数最多的"
        assert results[0]['error_count'] == 3, "word1 应该有3次错误"
        
        print("\n✓ 所有测试通过!")
    else:
        print(f"✗ MapReduce 分析失败: {status.get('error', 'Unknown error')}")
        return False
    
    # 清理测试文件
    if test_error_file.exists():
        test_error_file.unlink()
    if test_word_file.exists():
        test_word_file.unlink()
    
    # 清理临时 MapReduce 文件
    data_dir = Path('data')
    for file in data_dir.glob('mapreduce_output_*.txt'):
        file.unlink()
    
    return True


if __name__ == "__main__":
    try:
        success = test_mapreduce_service()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
