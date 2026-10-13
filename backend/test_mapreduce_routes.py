"""MapReduce API 路由测试"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from backend.main import app
from backend.repositories.error_record_repository import ErrorRecordRepository
from backend.repositories.word_repository import WordRepository
from backend.models import ErrorRecord, Word
from datetime import datetime
import uuid


client = TestClient(app)


def setup_test_data():
    """设置测试数据"""
    error_repo = ErrorRecordRepository()
    word_repo = WordRepository()
    
    # 创建测试单词
    test_words = [
        Word(
            id='test_word1',
            word='apple',
            definition='苹果',
            part_of_speech='noun',
            difficulty=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Word(
            id='test_word2',
            word='banana',
            definition='香蕉',
            part_of_speech='noun',
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
            user_id='api_test_user',
            word_id='test_word1',
            wrong_answer='aple',
            correct_answer='apple',
            timestamp=datetime.now()
        ),
        ErrorRecord(
            id=str(uuid.uuid4()),
            user_id='api_test_user',
            word_id='test_word1',
            wrong_answer='appl',
            correct_answer='apple',
            timestamp=datetime.now()
        ),
        ErrorRecord(
            id=str(uuid.uuid4()),
            user_id='api_test_user',
            word_id='test_word2',
            wrong_answer='bananna',
            correct_answer='banana',
            timestamp=datetime.now()
        )
    ]
    
    for error in test_errors:
        error_repo.save(error)
    
    print("测试数据设置完成")


def test_trigger_analysis():
    """测试触发 MapReduce 分析"""
    print("\n测试 POST /api/mapreduce/trigger...")
    
    response = client.post("/api/mapreduce/trigger?user_id=api_test_user")
    
    assert response.status_code == 200, f"状态码应该是 200，实际是 {response.status_code}"
    
    data = response.json()
    assert 'job_id' in data, "响应应该包含 job_id"
    assert 'message' in data, "响应应该包含 message"
    
    print(f"✓ 触发分析成功，作业ID: {data['job_id']}")
    
    return data['job_id']


def test_get_job_status(job_id: str):
    """测试获取作业状态"""
    print(f"\n测试 GET /api/mapreduce/status/{job_id}...")
    
    response = client.get(f"/api/mapreduce/status/{job_id}")
    
    assert response.status_code == 200, f"状态码应该是 200，实际是 {response.status_code}"
    
    data = response.json()
    assert 'status' in data, "响应应该包含 status"
    assert data['status'] in ['running', 'completed', 'failed'], f"状态应该是有效值，实际是 {data['status']}"
    
    print(f"✓ 获取状态成功: {data['status']}")
    
    return data['status']


def test_get_job_status_not_found():
    """测试获取不存在的作业状态"""
    print("\n测试 GET /api/mapreduce/status/nonexistent...")
    
    response = client.get("/api/mapreduce/status/nonexistent")
    
    assert response.status_code == 404, f"状态码应该是 404，实际是 {response.status_code}"
    
    print("✓ 正确返回 404 错误")


def test_get_analysis_results(job_id: str):
    """测试获取分析结果"""
    print(f"\n测试 GET /api/mapreduce/results?job_id={job_id}...")
    
    response = client.get(f"/api/mapreduce/results?user_id=api_test_user&job_id={job_id}&top_n=10")
    
    assert response.status_code == 200, f"状态码应该是 200，实际是 {response.status_code}"
    
    data = response.json()
    assert 'results' in data, "响应应该包含 results"
    assert 'total_count' in data, "响应应该包含 total_count"
    assert isinstance(data['results'], list), "results 应该是列表"
    
    print(f"✓ 获取结果成功，共 {data['total_count']} 个高频错词")
    
    if len(data['results']) > 0:
        print("\n高频错词列表:")
        for i, result in enumerate(data['results'], 1):
            print(f"{i}. {result['word']} - 错误次数: {result['error_count']}")
    
    return data


def test_get_analysis_results_without_job_id():
    """测试不指定 job_id 获取分析结果（应该触发新分析）"""
    print("\n测试 GET /api/mapreduce/results（不指定 job_id）...")
    
    response = client.get("/api/mapreduce/results?user_id=api_test_user&top_n=5")
    
    assert response.status_code == 200, f"状态码应该是 200，实际是 {response.status_code}"
    
    data = response.json()
    assert 'results' in data, "响应应该包含 results"
    
    print(f"✓ 获取结果成功（自动触发新分析），共 {data['total_count']} 个高频错词")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("MapReduce API 路由测试")
    print("=" * 60)
    
    # 设置测试数据
    setup_test_data()
    
    # 测试触发分析
    job_id = test_trigger_analysis()
    
    # 测试获取作业状态
    status = test_get_job_status(job_id)
    
    # 测试获取不存在的作业
    test_get_job_status_not_found()
    
    # 如果作业完成，测试获取结果
    if status == 'completed':
        test_get_analysis_results(job_id)
    
    # 测试不指定 job_id 获取结果
    test_get_analysis_results_without_job_id()
    
    print("\n" + "=" * 60)
    print("✓ 所有测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_all_tests()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ 测试失败: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
