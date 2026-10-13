"""测试复习路由"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_get_review_queue():
    """测试获取复习队列"""
    response = client.get("/api/review/queue?user_id=default_user")
    print(f"获取复习队列状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"复习队列长度: {len(data)}")
        if len(data) > 0:
            print(f"第一个单词: {data[0]}")
    else:
        print(f"错误: {response.json()}")


def test_get_review_info():
    """测试获取复习信息"""
    # 首先获取一个单词ID
    words_response = client.get("/api/words")
    if words_response.status_code == 200:
        words = words_response.json()
        if len(words) > 0:
            word_id = words[0]['id']
            response = client.get(f"/api/review/info/{word_id}?user_id=default_user")
            print(f"\n获取复习信息状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"复习信息: {data}")
            else:
                print(f"错误: {response.json()}")
        else:
            print("\n没有可用的单词进行测试")
    else:
        print("\n无法获取单词列表")


def test_submit_review_answer():
    """测试提交复习答案"""
    # 首先获取复习队列
    queue_response = client.get("/api/review/queue?user_id=default_user")
    
    if queue_response.status_code == 200:
        queue = queue_response.json()
        if len(queue) > 0:
            word = queue[0]
            
            # 提交正确答案
            response = client.post("/api/review/submit", json={
                "user_id": "default_user",
                "word_id": word['word_id'],
                "user_answer": word['word']
            })
            
            print(f"\n提交复习答案状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"答案验证结果: {data}")
            else:
                print(f"错误: {response.json()}")
        else:
            print("\n复习队列为空，无法测试提交答案")
    else:
        print("\n无法获取复习队列")


if __name__ == "__main__":
    print("=" * 50)
    print("测试复习路由")
    print("=" * 50)
    
    test_get_review_queue()
    test_get_review_info()
    test_submit_review_answer()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
