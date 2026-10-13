"""测试 API 路由的测试"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.repositories.word_repository import WordRepository


client = TestClient(app)


def test_start_test_endpoint():
    """测试开始测试端点"""
    response = client.post(
        "/api/test/start",
        json={
            "user_id": "test_user",
            "word_count": 2
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert "session_id" in data
    assert data["user_id"] == "test_user"
    assert data["word_count"] == 2
    assert len(data["words"]) == 2
    assert "start_time" in data
    
    # 验证单词只包含中文释义，不包含英文单词
    for word in data["words"]:
        assert "word_id" in word
        assert "definition" in word
        assert "part_of_speech" in word
        assert "difficulty" in word
        assert "word" not in word  # 不应该包含英文单词


def test_submit_answer_correct():
    """测试提交正确答案"""
    # 先开始测试
    start_response = client.post(
        "/api/test/start",
        json={
            "user_id": "test_user",
            "word_count": 1
        }
    )
    
    assert start_response.status_code == 201
    start_data = start_response.json()
    session_id = start_data["session_id"]
    word_id = start_data["words"][0]["word_id"]
    
    # 获取正确答案（从数据库）
    word_repo = WordRepository()
    word = word_repo.find_by_id(word_id)
    
    # 提交正确答案
    submit_response = client.post(
        "/api/test/submit",
        json={
            "session_id": session_id,
            "word_id": word_id,
            "user_answer": word.word
        }
    )
    
    assert submit_response.status_code == 200
    submit_data = submit_response.json()
    
    assert submit_data["is_correct"] is True
    assert submit_data["word_id"] == word_id
    assert submit_data["correct_answer"] is None  # 正确答案不返回


def test_submit_answer_incorrect():
    """测试提交错误答案"""
    # 先开始测试
    start_response = client.post(
        "/api/test/start",
        json={
            "user_id": "test_user",
            "word_count": 1
        }
    )
    
    assert start_response.status_code == 201
    start_data = start_response.json()
    session_id = start_data["session_id"]
    word_id = start_data["words"][0]["word_id"]
    
    # 提交错误答案
    submit_response = client.post(
        "/api/test/submit",
        json={
            "session_id": session_id,
            "word_id": word_id,
            "user_answer": "wrong_answer"
        }
    )
    
    assert submit_response.status_code == 200
    submit_data = submit_response.json()
    
    assert submit_data["is_correct"] is False
    assert submit_data["word_id"] == word_id
    assert submit_data["correct_answer"] is not None  # 错误时返回正确答案


def test_end_test_endpoint():
    """测试结束测试端点"""
    # 先开始测试
    start_response = client.post(
        "/api/test/start",
        json={
            "user_id": "test_user",
            "word_count": 2
        }
    )
    
    assert start_response.status_code == 201
    start_data = start_response.json()
    session_id = start_data["session_id"]
    
    # 提交一些答案
    for word in start_data["words"]:
        client.post(
            "/api/test/submit",
            json={
                "session_id": session_id,
                "word_id": word["word_id"],
                "user_answer": "test_answer"
            }
        )
    
    # 结束测试
    end_response = client.post(
        "/api/test/end",
        json={
            "session_id": session_id
        }
    )
    
    assert end_response.status_code == 200
    end_data = end_response.json()
    
    assert end_data["session_id"] == session_id
    assert end_data["total_count"] == 2
    assert "correct_count" in end_data
    assert "wrong_count" in end_data
    assert "accuracy" in end_data
    assert "duration" in end_data
    assert "timestamp" in end_data
    
    # 验证统计正确性
    assert end_data["correct_count"] + end_data["wrong_count"] == end_data["total_count"]


def test_get_test_results():
    """测试获取测试结果端点"""
    # 先开始并完成测试
    start_response = client.post(
        "/api/test/start",
        json={
            "user_id": "test_user",
            "word_count": 1
        }
    )
    
    start_data = start_response.json()
    session_id = start_data["session_id"]
    
    # 结束测试
    client.post(
        "/api/test/end",
        json={
            "session_id": session_id
        }
    )
    
    # 获取测试结果
    results_response = client.get(f"/api/test/results/{session_id}")
    
    assert results_response.status_code == 200
    results_data = results_response.json()
    
    assert results_data["session_id"] == session_id
    assert "total_count" in results_data
    assert "correct_count" in results_data
    assert "wrong_count" in results_data
    assert "accuracy" in results_data
    assert "duration" in results_data


def test_start_test_with_invalid_data():
    """测试使用无效数据开始测试"""
    response = client.post(
        "/api/test/start",
        json={
            "user_id": "",
            "word_count": 0
        }
    )
    
    assert response.status_code == 400


def test_submit_answer_with_invalid_session():
    """测试使用无效会话提交答案"""
    response = client.post(
        "/api/test/submit",
        json={
            "session_id": "invalid_session_id",
            "word_id": "some_word_id",
            "user_answer": "test"
        }
    )
    
    assert response.status_code == 400


def test_get_results_for_nonexistent_session():
    """测试获取不存在的会话结果"""
    response = client.get("/api/test/results/nonexistent_session_id")
    
    assert response.status_code == 404
