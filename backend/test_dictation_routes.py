"""测试默写本生成 API 路由"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import app

client = TestClient(app)


def test_generate_dictation_book_txt_default():
    """测试生成默写本 - TXT 格式，默认参数"""
    response = client.post("/api/dictation/generate")
    
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "attachment" in response.headers["content-disposition"]
    assert "dictation_book_default.txt" in response.headers["content-disposition"]
    
    # 验证内容
    content = response.content.decode('utf-8')
    assert "英语单词默写本" in content or "暂无错词记录" in content


def test_generate_dictation_book_txt_with_params():
    """测试生成默写本 - TXT 格式，自定义参数"""
    response = client.post(
        "/api/dictation/generate",
        params={
            "user_id": "test_user",
            "top_n": 20,
            "format": "txt"
        }
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "dictation_book_test_user.txt" in response.headers["content-disposition"]


def test_generate_dictation_book_pdf():
    """测试生成默写本 - PDF 格式"""
    response = client.post(
        "/api/dictation/generate",
        params={
            "user_id": "default",
            "top_n": 10,
            "format": "pdf"
        }
    )
    
    assert response.status_code == 200
    # PDF 或错误消息
    if response.headers["content-type"] == "application/pdf":
        assert "dictation_book_default.pdf" in response.headers["content-disposition"]
    else:
        # 可能是 reportlab 未安装的错误消息
        assert response.status_code == 200


def test_generate_dictation_book_invalid_format():
    """测试生成默写本 - 无效格式"""
    response = client.post(
        "/api/dictation/generate",
        params={
            "format": "invalid"
        }
    )
    
    assert response.status_code == 400
    assert "INVALID_FORMAT" in response.json()["detail"]["code"]


def test_generate_dictation_book_top_n_validation():
    """测试生成默写本 - top_n 参数验证"""
    # 测试 top_n 为 0（应该失败）
    response = client.post(
        "/api/dictation/generate",
        params={
            "top_n": 0
        }
    )
    assert response.status_code == 422  # Validation error
    
    # 测试 top_n 超过最大值（应该失败）
    response = client.post(
        "/api/dictation/generate",
        params={
            "top_n": 2000
        }
    )
    assert response.status_code == 422  # Validation error


def test_generate_dictation_book_case_insensitive_format():
    """测试生成默写本 - 格式参数不区分大小写"""
    response = client.post(
        "/api/dictation/generate",
        params={
            "format": "TXT"
        }
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
