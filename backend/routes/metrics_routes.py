"""Prometheus 指标暴露端点"""
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def get_metrics():
    """暴露 Prometheus 指标
    
    Prometheus 服务器会定期抓取这个端点
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
