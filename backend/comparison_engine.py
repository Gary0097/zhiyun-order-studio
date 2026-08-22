# -*- coding: utf-8 -*-
"""Explainable order/contract consistency comparison."""

from __future__ import annotations

from typing import Any

try:
    from .contract_engine import review_contract_text
    from .order_parser import parse_order_text
except ImportError:
    from contract_engine import review_contract_text
    from order_parser import parse_order_text


FIELDS = [
    ("customer_name", "party_a", "客户/甲方", "high"),
    ("product_name", "product_name", "产品名称", "high"),
    ("quantity", "quantity", "数量", "high"),
    ("promised_date", "promised_date", "交期", "high"),
    ("unit_price", "unit_price", "单价", "high"),
    ("payment_ratio", "payment_ratio", "付款比例", "medium"),
]


def _same(left: Any, right: Any) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)) < 0.000001
    return str(left).strip().casefold().replace(" ", "") == str(right).strip().casefold().replace(" ", "")


def compare_order_contract(order_text: str, contract_text: str) -> dict[str, Any]:
    order = parse_order_text(order_text)["order"]
    contract_review = review_contract_text(contract_text)
    contract = contract_review["contract"]
    checks, differences, unavailable = [], [], []
    for order_key, contract_key, label, severity in FIELDS:
        left, right = order.get(order_key), contract.get(contract_key)
        if left in (None, "") or right in (None, ""):
            unavailable.append({"field": label, "order_value": left, "contract_value": right, "reason": "一侧或双方缺少可比字段"})
            continue
        matched = _same(left, right)
        item = {"field": label, "order_value": left, "contract_value": right, "matched": matched, "severity": severity if not matched else "low"}
        checks.append(item)
        if not matched:
            differences.append(item)
    return {
        "consistent": not differences,
        "checks": checks,
        "differences": differences,
        "unavailable_fields": unavailable,
        "requires_human_confirmation": True,
        "summary": "发现%d项差异，%d项因数据缺失无法比较。" % (len(differences), len(unavailable)),
    }
