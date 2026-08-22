# -*- coding: utf-8 -*-
"""Explainable order-template matching and processing paths."""

from __future__ import annotations

from typing import Any

TEMPLATES = [
    {
        "id": "fob-export",
        "name": "FOB出口订单",
        "keywords": ["fob", "出口", "报关", "装运港", "目的港", "海运"],
        "required_fields": ["贸易条款", "装运港", "目的港", "报关资料", "币种"],
        "process_steps": ["确认贸易条款与币种", "核对装运港和目的港", "准备报关资料", "确认订舱与截关时间", "生成出口交付计划"],
    },
    {
        "id": "oem-processing",
        "name": "代工/OEM订单",
        "keywords": ["oem", "odm", "代工", "贴牌", "来料", "图纸", "定制"],
        "required_fields": ["图纸/规格", "来料方式", "品牌标识", "验收标准"],
        "process_steps": ["确认图纸与技术规格", "评估来料和产能", "确认样品及验收标准", "排产", "质量检验与交付"],
    },
    {
        "id": "promotion",
        "name": "促销活动订单",
        "keywords": ["促销", "活动", "大促", "赠品", "礼盒", "限时", "双11", "618"],
        "required_fields": ["活动日期", "活动渠道", "包装要求", "峰值数量"],
        "process_steps": ["确认活动窗口", "核对峰值需求", "确认促销包装", "锁定库存与产能", "制定活动交付预案"],
    },
    {
        "id": "standard",
        "name": "标准销售订单",
        "keywords": [],
        "required_fields": ["客户", "产品", "数量", "交期"],
        "process_steps": ["核对客户与产品", "确认价格和数量", "检查库存与产能", "确认交期", "生成标准工单"],
    },
]


def match_order_template(text: str) -> dict[str, Any]:
    normalized = text.casefold()
    candidates = []
    for template in TEMPLATES[:-1]:
        hits = [keyword for keyword in template["keywords"] if keyword.casefold() in normalized]
        score = min(100, len(hits) * 30)
        candidates.append({**template, "score": score, "matched_keywords": hits})
    candidates.sort(key=lambda item: (-item["score"], item["id"]))
    best = candidates[0] if candidates and candidates[0]["score"] else {**TEMPLATES[-1], "score": 50, "matched_keywords": []}
    alternatives = [item for item in candidates if item["score"] and item["id"] != best["id"]][:2]
    return {
        "template": best,
        "alternatives": alternatives,
        "confidence": "high" if best["score"] >= 60 else "medium" if best["score"] >= 50 else "low",
        "requires_human_confirmation": True,
        "reason": "命中关键词：" + "、".join(best["matched_keywords"]) if best["matched_keywords"] else "未识别到特殊订单关键词，暂按标准销售订单处理。",
    }
