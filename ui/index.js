(function () {
  var Q = window.QwenPaw;
  if (!Q || !Q.host || !Q.host.React || !Q.registerRoutes) return;
  var React = Q.host.React, antd = Q.host.antd, h = React.createElement;

  function request(path, body) {
    return Q.host.fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(function (response) {
      return response.json().then(function (data) { if (!response.ok) throw new Error(data.detail || "解析失败"); return data; });
    });
  }

  function OrderStudio() {
    var textState = React.useState("客户：海川制造；产品：伺服电机；数量：20台；交期：2026年9月10日");
    var text = textState[0], setText = textState[1];
    var resultState = React.useState(null), result = resultState[0], setResult = resultState[1];
    var loadingState = React.useState(false), loading = loadingState[0], setLoading = loadingState[1];
    var message = antd.App.useApp().message;
    function run() { setLoading(true); request("/zhiyun-order-studio/parse-text", { text: text }).then(setResult).catch(function (e) { message.error(e.message); }).finally(function () { setLoading(false); }); }
    var labels = { customer_name: "客户名称", product_name: "产品名称", quantity: "数量", unit: "单位", promised_date: "承诺交期" };
    return h("div", { style: { padding: 28, height: "100%", overflow: "auto", background: "#f7f8fa" } }, h("div", { style: { maxWidth: 1000, margin: "0 auto" } },
      h("h2", null, "Order Studio"), h("p", { style: { color: "#667085" } }, "粘贴微信、邮件或OCR识别后的订单文本，生成待确认的标准工单。"),
      h(antd.Input.TextArea, { value: text, rows: 7, onChange: function (e) { setText(e.target.value); }, placeholder: "输入客户、产品、数量和交期" }),
      h(antd.Button, { type: "primary", loading: loading, onClick: run, style: { marginTop: 12 } }, "解析订单"),
      result ? h(React.Fragment, null,
        h(antd.Alert, { style: { marginTop: 16 }, type: result.ready_for_review ? "success" : "warning", showIcon: true, message: result.ready_for_review ? "关键字段已提取，请人工确认" : "订单信息不完整", description: result.missing_fields.length ? "缺少：" + result.missing_fields.map(function (x) { return labels[x] || x; }).join("、") : "系统不会自动提交，确认后再进入订单流程。" }),
        h(antd.Card, { title: "标准工单预览", style: { marginTop: 16 } }, h(antd.Descriptions, { bordered: true, column: 2, items: Object.keys(labels).map(function (key) { return { key: key, label: labels[key], children: result.order[key] == null ? h(antd.Tag, { color: "orange" }, "待补充") : String(result.order[key]) }; }) })),
        h(antd.Card, { title: "提取证据", style: { marginTop: 16 } }, h(antd.List, { dataSource: result.evidence, renderItem: function (item) { return h(antd.List.Item, null, h(antd.Tag, null, labels[item.field] || item.field), item.source); } }))
      ) : null
    ));
  }
  Q.registerRoutes("zhiyun-order-studio", [{ path: "/apps/zhiyun-order-studio", component: OrderStudio, label: "Order Studio", icon: "📋", priority: 88 }]);
})();
