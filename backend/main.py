# -*- coding: utf-8 -*-
"""Order Studio HTTP and Agent entrypoint."""

from __future__ import annotations

import sys
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from qwenpaw.plugins.api import PluginApi

try:
    from .comparison_engine import compare_order_contract
    from .contract_engine import review_contract_text
    from .document_parser import extract_document_text
    from .order_parser import parse_order_text
    from .order_workflow import OrderWorkflowStore
    from .template_engine import match_order_template
except ImportError:
    backend_dir = str(Path(__file__).resolve().parent)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from comparison_engine import compare_order_contract
    from contract_engine import review_contract_text
    from document_parser import extract_document_text
    from order_parser import parse_order_text
    from order_workflow import OrderWorkflowStore
    from template_engine import match_order_template

router = APIRouter()
PLUGIN_VERSION = "0.7.3"


def _store() -> OrderWorkflowStore:
    try:
        return OrderWorkflowStore()
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(status_code=503, detail=f"持久化依赖不可用：{exc}") from exc


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


class ContractReviewRequest(TextRequest):
    user_position: str = Field(default="采购方", max_length=30)


class DocumentRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1)


class CompareRequest(BaseModel):
    order_text: str = Field(min_length=1, max_length=20000)
    contract_text: str = Field(min_length=1, max_length=50000)


class ProjectRequest(BaseModel):
    source_text: str = Field(max_length=20000)
    source_channel: str
    name: str | None = Field(default=None, max_length=100)


class ReviewRequest(BaseModel):
    action: str
    reviewer: str = Field(min_length=1, max_length=100)
    note: str | None = Field(default=None, max_length=1000)
    order: dict[str, Any] | None = None


class ExceptionRequest(BaseModel):
    order_text: str = Field(min_length=1, max_length=20000)
    contract_text: str = Field(min_length=1, max_length=50000)
    project_id: str | None = None


class ExceptionReviewRequest(BaseModel):
    action: str
    reviewer: str = Field(min_length=1, max_length=100)
    selected_path: str | None = Field(default=None, max_length=2000)
    wording: str | None = Field(default=None, max_length=5000)
    note: str | None = Field(default=None, max_length=2000)


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "available", "version": PLUGIN_VERSION}


@router.post("/parse-text")
async def parse_text(request: TextRequest) -> dict[str, Any]:
    try:
        return parse_order_text(request.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/projects")
async def create_project(request: ProjectRequest) -> dict[str, Any]:
    """Persist real user input and execute an auditable formatting run."""
    try:
        return _store().create_project(request.source_text, request.source_channel, request.name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"持久化依赖不可用：{exc}") from exc


@router.get("/projects/{project_id}")
async def get_project(project_id: str) -> dict[str, Any]:
    try:
        return _store().get_project(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="项目不存在") from exc
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"持久化依赖不可用：{exc}") from exc


@router.post("/projects/{project_id}/reviews")
async def review_project(project_id: str, request: ReviewRequest) -> dict[str, Any]:
    try:
        return _store().review(project_id, request.action, request.reviewer, request.note, request.order)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="项目不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"持久化依赖不可用：{exc}") from exc


@router.get("/projects/{project_id}/export")
async def export_project(project_id: str, format: str = "json") -> Response:
    try:
        content, media_type = _store().export(project_id, format)
        return Response(content=content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="order.{format}"'})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="项目不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"持久化依赖不可用：{exc}") from exc


@router.post("/templates/match")
async def match_template(request: TextRequest) -> dict[str, Any]:
    return match_order_template(request.text)


@router.post("/contracts/review")
async def review_contract(request: ContractReviewRequest) -> dict[str, Any]:
    try:
        return review_contract_text(request.text, request.user_position)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/contracts/extract-file")
async def extract_contract_file(request: DocumentRequest) -> dict[str, Any]:
    try:
        return extract_document_text(request.filename, request.content_base64)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/contracts/compare-order")
async def compare_contract_order(request: CompareRequest) -> dict[str, Any]:
    try:
        return compare_order_contract(request.order_text, request.contract_text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/exceptions")
async def create_exception(request: ExceptionRequest) -> dict[str, Any]:
    try:
        return _store().create_exception(request.order_text, request.contract_text, request.project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="订单项目不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"持久化依赖不可用：{exc}") from exc


@router.get("/exceptions/{case_id}")
async def get_exception(case_id: str) -> dict[str, Any]:
    try:
        return _store().get_exception(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="异常记录不存在") from exc


@router.post("/exceptions/{case_id}/reviews")
async def review_exception(case_id: str, request: ExceptionReviewRequest) -> dict[str, Any]:
    try:
        return _store().review_exception(case_id, request.action, request.reviewer,
                                         request.selected_path, request.wording, request.note)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="异常记录不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/exceptions/{case_id}/retry")
async def retry_exception(case_id: str) -> dict[str, Any]:
    try:
        return _store().retry_exception(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="异常记录不存在") from exc


@router.get("/exceptions/{case_id}/export")
async def export_exception(case_id: str) -> Response:
    try:
        content, media_type = _store().export_exception(case_id)
        return Response(content=content, media_type=media_type,
                        headers={"Content-Disposition": 'attachment; filename="exception-plan.json"'})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="异常记录不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def format_customer_order(text: str) -> dict[str, Any]:
    """Extract a reviewable standard work order from customer text."""
    return parse_order_text(text)


def run_customer_order_workflow(text: str, source_channel: str) -> dict[str, Any]:
    """Create a durable Project/Run/Step/Artifact awaiting human review."""
    return _store().create_project(text, source_channel)


def recommend_order_template(text: str) -> dict[str, Any]:
    """Recommend a reviewable order workflow template from source text."""
    return match_order_template(text)


def extract_and_review_contract(text: str, user_position: str = "采购方") -> dict[str, Any]:
    """Extract contract terms and return evidence-based risk findings."""
    return review_contract_text(text, user_position)


def verify_order_contract_consistency(order_text: str, contract_text: str) -> dict[str, Any]:
    """Compare order and contract values without modifying either source."""
    return compare_order_contract(order_text, contract_text)


def run_order_exception_workflow(order_text: str, contract_text: str) -> dict[str, Any]:
    """Create a durable exception case with evidence-based paths and wording."""
    return _store().create_exception(order_text, contract_text)


class OrderStudioPlugin:
    def register(self, api: PluginApi) -> None:
        api.register_http_router(router, prefix="/zhiyun-order-studio", tags=["zhiyun-order-studio"])
        api.register_tool(
            tool_name="format_customer_order",
            tool_func=format_customer_order,
            description="从微信、邮件或OCR结果文本中提取客户、产品、数量和交期，返回原文证据、缺失字段和待人工确认的标准工单。",
            icon="📋",
            tool_type="file",
        )
        api.register_tool(
            tool_name="run_customer_order_workflow",
            tool_func=run_customer_order_workflow,
            description="持久化用户提供的微信、邮件或OCR订单原文，创建项目、运行、步骤和含来源证据的待审阅产物。",
            icon="▶️",
            tool_type="internal",
        )
        api.register_tool(
            tool_name="extract_and_review_contract",
            tool_func=extract_and_review_contract,
            description="提取合同双方、金额、付款、交付、违约和争议条款，返回原文证据、缺失项与红黄绿风险初筛；不构成法律意见。",
            icon="📑",
            tool_type="file",
        )
        api.register_tool(
            tool_name="recommend_order_template",
            tool_func=recommend_order_template,
            description="识别标准、FOB出口、代工/OEM或促销订单，返回命中依据、必填信息与处理步骤；结果必须人工确认。",
            icon="🧩",
            tool_type="internal",
        )
        api.register_tool(
            tool_name="verify_order_contract_consistency",
            tool_func=verify_order_contract_consistency,
            description="对比订单与合同的客户、产品、数量、交期、单价和付款比例，返回差异与缺失字段；结果必须人工确认。",
            icon="🔎",
            tool_type="internal",
        )
        api.register_tool(
            tool_name="run_order_exception_workflow",
            tool_func=run_order_exception_workflow,
            description="基于真实订单和合同证据创建异常记录，推荐处理路径和回复话术，并等待具名人员审阅；不会自动执行或修改业务订单。",
            icon="🚨",
            tool_type="internal",
        )


plugin = OrderStudioPlugin()
