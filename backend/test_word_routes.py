"""测试单词管理 API 路由"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    print("✓ 健康检查端点正常")


def test_add_word():
    """测试添加单词端点"""
    word_data = {
        "word": "hello",
        "definition": "你好",
        "part_of_speech": "noun",
        "difficulty": 1
    }
    
    response = client.post("/api/words", json=word_data)
    print(f"添加单词响应状态码: {response.status_code}")
    print(f"添加单词响应内容: {response.json()}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["word"] == "hello"
    assert data["definition"] == "你好"
    assert data["part_of_speech"] == "noun"
    assert data["difficulty"] == 1
    assert "id" in data
    print("✓ 添加单词端点正常")
    
    return data["id"]


def test_get_words():
    """测试获取单词列表端点"""
    response = client.get("/api/words")
    print(f"获取单词列表响应状态码: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"✓ 获取单词列表端点正常，共 {len(data)} 个单词")


def test_get_words_with_filter():
    """测试带过滤条件的获取单词列表"""
    response = client.get("/api/words?difficulty=1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"✓ 按难度过滤单词列表正常，共 {len(data)} 个单词")


def test_mark_as_mastered():
    """测试标记单词为已掌握端点"""
    # 先添加一个单词
    word_data = {
        "word": "world",
        "definition": "世界",
        "part_of_speech": "noun",
        "difficulty": 2
    }
    
    add_response = client.post("/api/words", json=word_data)
    word_id = add_response.json()["id"]
    
    # 标记为已掌握
    response = client.put(f"/api/words/{word_id}/master?user_id=test_user")
    print(f"标记已掌握响应状态码: {response.status_code}")
    print(f"标记已掌握响应内容: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["word_id"] == word_id
    assert data["user_id"] == "test_user"
    print("✓ 标记单词为已掌握端点正常")


def test_add_duplicate_word():
    """测试添加重复单词（应该失败）"""
    word_data = {
        "word": "duplicate",
        "definition": "重复",
        "part_of_speech": "noun",
        "difficulty": 1
    }
    
    # 第一次添加
    response1 = client.post("/api/words", json=word_data)
    assert response1.status_code == 201
    
    # 第二次添加（应该失败）
    response2 = client.post("/api/words", json=word_data)
    print(f"添加重复单词响应状态码: {response2.status_code}")
    assert response2.status_code == 400
    print("✓ 重复单词检测正常")


def test_add_invalid_word():
    """测试添加无效单词（应该失败）"""
    # 缺少必填字段
    word_data = {
        "word": "invalid"
    }
    
    response = client.post("/api/words", json=word_data)
    print(f"添加无效单词响应状态码: {response.status_code}")
    assert response.status_code == 422  # FastAPI 验证错误
    print("✓ 输入验证正常")


def test_import_words():
    """测试批量导入单词端点"""
    # 创建测试文件内容
    test_content = """apple\t苹果\tnoun\t1
banana\t香蕉\tnoun\t1
run\t跑\tverb\t2
beautiful\t美丽的\tadj\t3"""
    
    # 创建临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_path = f.name
    
    try:
        # 读取文件并上传
        with open(temp_path, 'rb') as f:
            files = {'file': ('test_words.txt', f, 'text/plain')}
            response = client.post("/api/words/import", files=files)
        
        print(f"批量导入响应状态码: {response.status_code}")
        print(f"批量导入响应内容: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] >= 0
        assert data["total_lines"] == 4
        print(f"✓ 批量导入端点正常，成功导入 {data['success_count']} 个单词")
    
    finally:
        # 清理临时文件
        os.unlink(temp_path)


def test_mark_nonexistent_word():
    """测试标记不存在的单词（应该失败）"""
    response = client.put("/api/words/nonexistent-id/master?user_id=test_user")
    print(f"标记不存在单词响应状态码: {response.status_code}")
    assert response.status_code == 404
    print("✓ 不存在单词检测正常")


if __name__ == "__main__":
    print("开始测试单词管理 API 路由...\n")
    
    try:
        test_health_check()
        test_add_word()
        test_get_words()
        test_get_words_with_filter()
        test_mark_as_mastered()
        test_add_duplicate_word()
        test_add_invalid_word()
        test_import_words()
        test_mark_nonexistent_word()
        
        print("\n✅ 所有测试通过！")
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
