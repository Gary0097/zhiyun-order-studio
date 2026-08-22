# -*- coding: utf-8 -*-
"""Deterministic Chinese order text extraction with review evidence."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

DATE_PATTERN = re.compile(r"(?:交期|交货日期|要求到货|到货日期)\s*[：:]?\s*(\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}日?)")
ORDER_DATE_PATTERN = re.compile(r"(?:下单日期|订单日期)\s*[：:]?\s*(\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}日?)")
ORDER_NO_PATTERN = re.compile(r"(?:订单号|采购单号|PO号|PO)\s*[：:#]?\s*([A-Za-z0-9_-]{2,50})", re.I)
QUANTITY_PATTERN = re.compile(r"(?:数量|订购|采购)\s*[：:]?\s*(\d+(?:\.\d+)?)\s*(台|件|套|个|箱|吨|kg|千克)?", re.I)
CUSTOMER_PATTERN = re.compile(r"(?:客户|公司|采购方|甲方)\s*[：:]?\s*([^，,；;\n]{2,40})")
PRODUCT_PATTERN = re.compile(r"(?:品名|产品|物料|设备)\s*[：:]?\s*([^，,；;\n]{2,60})")
UNIT_PRICE_PATTERN = re.compile(r"(?:单价)\s*[：:]?\s*[￥¥]?([\d,.]+)")
PAYMENT_RATIO_PATTERN = re.compile(r"(?:付款比例|预付款比例|首付款比例)\s*[：:]?\s*(\d+(?:\.\d+)?)%")


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
    order_date = ORDER_DATE_PATTERN.search(source)
    order_no = ORDER_NO_PATTERN.search(source)
    unit_price = UNIT_PRICE_PATTERN.search(source)
    payment_ratio = PAYMENT_RATIO_PATTERN.search(source)
    order = {
        "order_no": order_no.group(1).strip() if order_no else None,
        "customer_name": customer.group(1).strip() if customer else None,
        "product_name": product.group(1).strip() if product else None,
        "quantity": float(quantity.group(1)) if quantity else None,
        "unit": quantity.group(2) if quantity and quantity.group(2) else None,
        "promised_date": _normalize_date(delivery.group(1)) if delivery else None,
        "unit_price": float(unit_price.group(1).replace(",", "")) if unit_price else None,
        "payment_ratio": float(payment_ratio.group(1)) if payment_ratio else None,
        "order_date": _normalize_date(order_date.group(1)) if order_date else None,
        "status": None,
        "progress": None,
        "source_text": source,
    }
    required = ["order_no", "customer_name", "product_name", "quantity", "order_date", "promised_date"]
    missing = [field for field in required if order[field] in (None, "")]
    evidence = []
    for field, match in [("order_no", order_no), ("customer_name", customer), ("product_name", product), ("quantity", quantity), ("order_date", order_date), ("promised_date", delivery), ("unit_price", unit_price), ("payment_ratio", payment_ratio)]:
        if match:
            evidence.append({"field": field, "source": match.group(0)})
    return {
        "order": order,
        "missing_fields": missing,
        "evidence": evidence,
        "ready_for_review": not missing,
        "requires_human_confirmation": True,
    }
