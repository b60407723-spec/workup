"""统计 API 路由测试"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_get_overall_stats():
    """测试获取总体统计"""
    response = client.get("/api/stats/overall?user_id=test_user")
    print(f"\n总体统计响应状态: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证响应包含所有必需字段
    assert 'total_words' in data
    assert 'mastered_count' in data
    assert 'learning_count' in data
    assert 'reviewing_count' in data
    assert 'unlearned_count' in data
    assert 'test_count' in data
    assert 'average_accuracy' in data
    
    # 验证数据类型
    assert isinstance(data['total_words'], int)
    assert isinstance(data['mastered_count'], int)
    assert isinstance(data['learning_count'], int)
    assert isinstance(data['test_count'], int)
    assert isinstance(data['average_accuracy'], (int, float))
    
    print("✓ 总体统计测试通过")


def test_get_difficulty_distribution():
    """测试获取难度分布"""
    response = client.get("/api/stats/difficulty?user_id=test_user")
    print(f"\n难度分布响应状态: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证包含所有难度等级
    for i in range(1, 6):
        difficulty_key = f'difficulty_{i}'
        assert difficulty_key in data
        
        difficulty_data = data[difficulty_key]
        assert 'total' in difficulty_data
        assert 'mastered' in difficulty_data
        assert 'learning' in difficulty_data
        assert 'reviewing' in difficulty_data
        assert 'error_rate' in difficulty_data
    
    print("✓ 难度分布测试通过")


def test_get_pos_analysis():
    """测试获取词性分析"""
    response = client.get("/api/stats/pos?user_id=test_user")
    print(f"\n词性分析响应状态: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证响应结构
    assert 'data' in data
    assert isinstance(data['data'], dict)
    
    # 如果有数据，验证数据结构
    for pos, pos_data in data['data'].items():
        assert 'total' in pos_data
        assert 'mastered' in pos_data
        assert 'learning' in pos_data
        assert 'reviewing' in pos_data
        assert 'error_count' in pos_data
    
    print("✓ 词性分析测试通过")


def test_get_time_trend():
    """测试获取时间趋势"""
    response = client.get("/api/stats/trend?user_id=test_user&granularity=day")
    print(f"\n时间趋势响应状态: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证响应包含所有必需字段
    assert 'dates' in data
    assert 'learned_words' in data
    assert 'test_count' in data
    assert 'error_count' in data
    
    # 验证数据类型
    assert isinstance(data['dates'], list)
    assert isinstance(data['learned_words'], list)
    assert isinstance(data['test_count'], list)
    assert isinstance(data['error_count'], list)
    
    # 验证所有列表长度相同
    assert len(data['dates']) == len(data['learned_words'])
    assert len(data['dates']) == len(data['test_count'])
    assert len(data['dates']) == len(data['error_count'])
    
    print("✓ 时间趋势测试通过")


def test_get_time_trend_with_date_range():
    """测试带日期范围的时间趋势"""
    response = client.get(
        "/api/stats/trend?user_id=test_user&start_date=2024-01-01&end_date=2024-01-31&granularity=week"
    )
    print(f"\n带日期范围的时间趋势响应状态: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'dates' in data
    assert 'learned_words' in data
    assert 'test_count' in data
    assert 'error_count' in data
    
    print("✓ 带日期范围的时间趋势测试通过")


def test_invalid_granularity():
    """测试无效的时间粒度"""
    response = client.get("/api/stats/trend?user_id=test_user&granularity=month")
    print(f"\n无效时间粒度响应状态: {response.status_code}")
    
    assert response.status_code == 400
    data = response.json()
    assert 'detail' in data
    
    print("✓ 无效时间粒度测试通过")


if __name__ == "__main__":
    print("=" * 60)
    print("开始测试统计 API 路由")
    print("=" * 60)
    
    try:
        test_get_overall_stats()
        test_get_difficulty_distribution()
        test_get_pos_analysis()
        test_get_time_trend()
        test_get_time_trend_with_date_range()
        test_invalid_granularity()
        
        print("\n" + "=" * 60)
        print("所有测试通过！✓")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
