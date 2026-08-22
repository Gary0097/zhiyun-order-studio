# -*- coding: utf-8 -*-
"""Evidence-based order exception classification and handling suggestions."""

from __future__ import annotations

from typing import Any

try:
    from .comparison_engine import compare_order_contract
    from .contract_engine import review_contract_text
except ImportError:
    from comparison_engine import compare_order_contract
    from contract_engine import review_contract_text


POLICIES = {
    "交期": ("交付协调", "核实产能与物料后，与客户确认可承诺交期。", ["核对产能和物料", "形成可承诺日期", "由业务负责人确认", "回复客户并留痕"]),
    "数量": ("数量复核", "订单与合同数量不一致，请确认分批交付或修订合同。", ["核对原始订单", "核对合同数量", "确认分批或修订方案", "双方书面确认"]),
    "单价": ("商务复核", "订单与合同单价不一致，请暂停提交并由商务人员复核。", ["核对报价和版本", "计算差额", "商务负责人确认", "更新工单或合同"]),
    "付款比例": ("付款条款复核", "付款比例存在差异，请在执行前确认最终付款节点。", ["核对付款条款", "评估资金风险", "负责人确认", "形成书面补充说明"]),
    "客户/甲方": ("主体复核", "客户主体不一致，请核对签约主体和订单归属。", ["核验客户主体", "核验开票与收货信息", "负责人确认", "修正后重新校验"]),
    "产品名称": ("产品复核", "产品名称不一致，请核对规格、型号和版本。", ["核对产品规格", "确认替代或修订", "技术/商务确认", "更新一致性结果"]),
    "合同风险": ("合同风险复核", "合同存在高风险或缺失条款，请由业务负责人和法务复核。", ["查看原文证据", "确认风险承担方", "形成修改意见", "双方确认后执行"]),
}


def build_exception_recommendation(order_text: str, contract_text: str) -> dict[str, Any]:
    """Return deterministic recommendations derived only from source evidence."""
    comparison = compare_order_contract(order_text, contract_text)
    contract = review_contract_text(contract_text)
    categories = [item["field"] for item in comparison["differences"]]
    if contract["overall_risk"] == "high" or contract["missing_clauses"]:
        categories.append("合同风险")
    categories = list(dict.fromkeys(categories))
    recommendations = []
    for category in categories:
        title, wording, path = POLICIES.get(category, POLICIES["合同风险"])
        recommendations.append({
            "category": category,
            "title": title,
            "suggested_wording": wording,
            "handling_path": path,
            "requires_human_confirmation": True,
        })
    return {
        "categories": categories,
        "comparison": comparison,
        "contract_risk": {
            "overall_risk": contract["overall_risk"],
            "missing_clauses": contract["missing_clauses"],
            "findings": contract["findings"],
        },
        "recommendations": recommendations,
        "status": "no_exception" if not categories else "pending_review",
        "disclaimer": "建议来自当前订单、合同证据与固定业务规则；执行前必须由具名人员确认。",
    }
