# -*- coding: utf-8 -*-
"""Order Studio HTTP and Agent entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from qwenpaw.plugins.api import PluginApi

try:
    from .contract_engine import review_contract_text
    from .order_parser import parse_order_text
    from .template_engine import match_order_template
except ImportError:
    backend_dir = str(Path(__file__).resolve().parent)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from contract_engine import review_contract_text
    from order_parser import parse_order_text
    from template_engine import match_order_template

router = APIRouter()


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


class ContractReviewRequest(TextRequest):
    user_position: str = Field(default="采购方", max_length=30)


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "available", "version": "0.4.0"}


@router.post("/parse-text")
async def parse_text(request: TextRequest) -> dict[str, Any]:
    try:
        return parse_order_text(request.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/templates/match")
async def match_template(request: TextRequest) -> dict[str, Any]:
    return match_order_template(request.text)


@router.post("/contracts/review")
async def review_contract(request: ContractReviewRequest) -> dict[str, Any]:
    try:
        return review_contract_text(request.text, request.user_position)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def format_customer_order(text: str) -> dict[str, Any]:
    """Extract a reviewable standard work order from customer text."""
    return parse_order_text(text)


def recommend_order_template(text: str) -> dict[str, Any]:
    """Recommend a reviewable order workflow template from source text."""
    return match_order_template(text)


def extract_and_review_contract(text: str, user_position: str = "采购方") -> dict[str, Any]:
    """Extract contract terms and return evidence-based risk findings."""
    return review_contract_text(text, user_position)


class OrderStudioPlugin:
    def register(self, api: PluginApi) -> None:
        api.register_http_router(router, prefix="/zhiyun-order-studio", tags=["zhiyun-order-studio"])
        api.register_tool(
            tool_name="format_customer_order",
            tool_func=format_customer_order,
            description="从微信、邮件或OCR结果文本中提取客户、产品、数量和交期，返回原文证据、缺失字段和待人工确认的标准工单。",
            icon="📋",
            tool_type="filesystem",
        )
        api.register_tool(
            tool_name="extract_and_review_contract",
            tool_func=extract_and_review_contract,
            description="提取合同双方、金额、付款、交付、违约和争议条款，返回原文证据、缺失项与红黄绿风险初筛；不构成法律意见。",
            icon="📑",
            tool_type="filesystem",
        )
        api.register_tool(
            tool_name="recommend_order_template",
            tool_func=recommend_order_template,
            description="识别标准、FOB出口、代工/OEM或促销订单，返回命中依据、必填信息与处理步骤；结果必须人工确认。",
            icon="🧩",
            tool_type="filesystem",
        )


plugin = OrderStudioPlugin()
