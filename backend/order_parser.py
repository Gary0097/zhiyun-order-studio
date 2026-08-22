# -*- coding: utf-8 -*-
"""Deterministic Chinese order text extraction with review evidence."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

DATE_PATTERN = re.compile(r"(?:交期|交货日期|要求到货|到货日期)\s*[：:]?\s*(\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}日?)")
QUANTITY_PATTERN = re.compile(r"(?:数量|订购|采购)\s*[：:]?\s*(\d+(?:\.\d+)?)\s*(台|件|套|个|箱|吨|kg|千克)?", re.I)
CUSTOMER_PATTERN = re.compile(r"(?:客户|公司|采购方|甲方)\s*[：:]?\s*([^，,；;\n]{2,40})")
PRODUCT_PATTERN = re.compile(r"(?:品名|产品|物料|设备)\s*[：:]?\s*([^，,；;\n]{2,60})")


def _normalize_date(value: str) -> str | None:
    clean = value.strip().replace("年", "-").replace("月", "-").replace("日", "").replace("/", ".")
    parts = re.split(r"[-.]", clean)
    try:
        return date(int(parts[0]), int(parts[1]), int(parts[2])).isoformat()
    except (ValueError, IndexError):
        return None


def parse_order_text(text: str) -> dict[str, Any]:
    """Extract a reviewable work order; never invent absent values."""
    source = text.strip()
    if not source:
        raise ValueError("订单文本不能为空")
    customer = CUSTOMER_PATTERN.search(source)
    product = PRODUCT_PATTERN.search(source)
    quantity = QUANTITY_PATTERN.search(source)
    delivery = DATE_PATTERN.search(source)
    order = {
        "customer_name": customer.group(1).strip() if customer else None,
        "product_name": product.group(1).strip() if product else None,
        "quantity": float(quantity.group(1)) if quantity else None,
        "unit": quantity.group(2) if quantity and quantity.group(2) else None,
        "promised_date": _normalize_date(delivery.group(1)) if delivery else None,
        "source_text": source,
    }
    required = ["customer_name", "product_name", "quantity", "promised_date"]
    missing = [field for field in required if order[field] in (None, "")]
    evidence = []
    for field, match in [("customer_name", customer), ("product_name", product), ("quantity", quantity), ("promised_date", delivery)]:
        if match:
            evidence.append({"field": field, "source": match.group(0)})
    return {
        "order": order,
        "missing_fields": missing,
        "evidence": evidence,
        "ready_for_review": not missing,
        "requires_human_confirmation": True,
    }
