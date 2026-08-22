# -*- coding: utf-8 -*-
"""Evidence-based commercial contract extraction and risk screening.

This deterministic first version never invents missing terms. It is a business
review aid, not a substitute for legal advice.
"""

from __future__ import annotations

import re
from typing import Any


FIELD_PATTERNS = {
    "contract_no": [r"(?:合同编号|编号)\s*[：:]\s*([^\s，,；;]+)"],
    "party_a": [r"(?:甲方|买方|采购方)\s*[：:]\s*([^\n；;]+)"],
    "party_b": [r"(?:乙方|卖方|供应方)\s*[：:]\s*([^\n；;]+)"],
    "amount": [r"(?:合同总?金额|总价|价款)\s*[：:]?\s*([人民币￥¥]?[\d,.]+\s*元?)"],
    "payment_terms": [r"((?:付款|支付)[^。；;\n]{2,80})"],
    "delivery_terms": [r"((?:交付|交货)[^。；;\n]{2,80})"],
    "breach_terms": [r"((?:违约|赔偿)[^。；;\n]{2,100})"],
    "governing_law": [r"((?:适用法律|管辖|仲裁)[^。；;\n]{2,100})"],
}


def _extract(text: str, patterns: list[str]) -> tuple[str | None, str | None]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip(" ：:，,。")
            return value, match.group(0).strip()
    return None, None


def _finding(level: str, category: str, evidence: str, issue: str, suggestion: str) -> dict[str, str]:
    return {"level": level, "category": category, "evidence": evidence, "issue": issue, "suggestion": suggestion}


def review_contract_text(text: str, user_position: str = "采购方") -> dict[str, Any]:
    if not text or not text.strip():
        raise ValueError("合同文本不能为空")
    text = text.strip()
    fields: dict[str, str | None] = {}
    evidence: list[dict[str, str]] = []
    for field, patterns in FIELD_PATTERNS.items():
        value, source = _extract(text, patterns)
        fields[field] = value
        if source:
            evidence.append({"field": field, "source": source})

    findings: list[dict[str, str]] = []
    blanks = re.findall(r"(?:TBD|待定|____+|\[\s*(?:金额|日期|名称|填写)\s*\])", text, re.IGNORECASE)
    if blanks:
        findings.append(_finding("high", "文本完整性", "、".join(blanks[:5]), "合同存在未填写字段，关键义务可能无法确认。", "签署前补齐所有空白项并由双方确认。"))
    if fields["payment_terms"] is None:
        findings.append(_finding("high", "付款条款", "未检出付款或支付条款", "付款节点、账期或付款条件缺失。", "明确预付款、进度款、验收款比例及付款期限。"))
    elif re.search(r"全额预付|100%\s*预付|先款后货", fields["payment_terms"] or "", re.IGNORECASE):
        findings.append(_finding("high" if user_position == "采购方" else "medium", "付款条款", fields["payment_terms"] or "", "采购方资金暴露较高，缺少交付保障。", "考虑分阶段付款，并将尾款与验收挂钩。"))
    if fields["delivery_terms"] is None:
        findings.append(_finding("high", "交付条件", "未检出交付或交货条款", "交付日期、地点或验收衔接不明确。", "补充明确交期、交付地点、运输责任和验收期限。"))
    if fields["breach_terms"] is None:
        findings.append(_finding("medium", "违约责任", "未检出违约或赔偿条款", "延期、质量不合格等情形缺少责任约束。", "补充延期交付、质量问题和解除合同的责任规则。"))
    elif re.search(r"无限|全部损失|任何损失", fields["breach_terms"] or ""):
        findings.append(_finding("high", "违约责任", fields["breach_terms"] or "", "责任范围可能无上限或过于宽泛。", "明确责任上限、直接损失范围及合理例外。"))
    if fields["governing_law"] is None:
        findings.append(_finding("medium", "争议解决", "未检出适用法律、管辖或仲裁条款", "发生争议时解决地点和方式不确定。", "约定适用法律及法院管辖或仲裁机构。"))

    referenced = sorted(set(re.findall(r"(?:附件|附表|清单)[一二三四五六七八九十A-Z0-9]*", text)))
    missing_clauses = [name for key, name in (("amount", "合同金额"), ("payment_terms", "付款条款"), ("delivery_terms", "交付条件"), ("breach_terms", "违约责任"), ("governing_law", "争议解决")) if fields[key] is None]
    rank = {"low": 1, "medium": 2, "high": 3}
    overall = max((item["level"] for item in findings), key=lambda level: rank[level], default="low")
    return {
        "contract": fields,
        "evidence": evidence,
        "findings": findings,
        "missing_clauses": missing_clauses,
        "referenced_attachments": referenced,
        "overall_risk": overall,
        "user_position": user_position,
        "requires_human_confirmation": True,
        "disclaimer": "本结果仅用于企业内部风险初筛，不构成法律意见；签署前应由业务负责人和专业法务复核。",
    }
