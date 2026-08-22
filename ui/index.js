(function () {
  var Q = window.QwenPaw;
  if (!Q || !Q.host || !Q.host.React || !Q.registerRoutes) return;
  var React = Q.host.React, antd = Q.host.antd, h = React.createElement;

  function request(path, body) {
    return Q.host.fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(function (response) {
      return response.json().then(function (data) { if (!response.ok) throw new Error(data.detail || "操作失败"); return data; });
    });
  }

  function OrderStudio() {
    var textState = React.useState("订单号：PO-20260822-01；下单日期：2026年8月22日；客户：海川制造；产品：伺服电机；数量：20台；交期：2026年9月10日");
    var text = textState[0], setText = textState[1];
    var resultState = React.useState(null), result = resultState[0], setResult = resultState[1];
    var draftState = React.useState({}), draft = draftState[0], setDraft = draftState[1];
    var loadingState = React.useState(false), loading = loadingState[0], setLoading = loadingState[1];
    var message = antd.App.useApp().message;
    var fields = [
      ["order_no", "订单编号", true], ["order_date", "下单日期", true], ["customer_name", "客户名称", true],
      ["product_name", "产品名称", true], ["quantity", "数量", true], ["promised_date", "承诺交期", true],
      ["status", "订单状态", true], ["progress", "完成进度", true]
    ];
    function run() {
      setLoading(true);
      request("/zhiyun-order-studio/parse-text", { text: text }).then(function (data) {
        setResult(data); setDraft(Object.assign({}, data.order, { status: data.order.status || "待排产", progress: data.order.progress == null ? 0 : data.order.progress }));
      }).catch(function (e) { message.error(e.message); }).finally(function () { setLoading(false); });
    }
    function update(name, value) { var next = Object.assign({}, draft); next[name] = value; setDraft(next); }
    function confirm() {
      var missing = fields.filter(function (item) { return item[2] && (draft[item[0]] === null || draft[item[0]] === undefined || draft[item[0]] === ""); });
      if (missing.length) { message.warning("请补齐：" + missing.map(function (item) { return item[1]; }).join("、")); return; }
      var row = {};
      fields.forEach(function (item) { row[item[0]] = item[0] === "quantity" || item[0] === "progress" ? Number(draft[item[0]]) : draft[item[0]]; });
      setLoading(true);
      request("/zhiyun-data-core/imports/orders/preview", { rows: [row], source_name: "Order Studio人工确认" }).then(function (preview) {
        if (preview.error_count) throw new Error(preview.errors.map(function (item) { return item.errors.join("，"); }).join("；"));
        return request("/zhiyun-data-core/imports/orders/commit", { rows: [row], source_name: "Order Studio人工确认" });
      }).then(function (saved) { message.success("标准工单已写入统一数据库，批次：" + saved.batch_id); })
        .catch(function (e) { message.error(e.message); }).finally(function () { setLoading(false); });
    }
    var evidenceLabels = { order_no: "订单编号", order_date: "下单日期", customer_name: "客户名称", product_name: "产品名称", quantity: "数量", promised_date: "承诺交期" };
    return h("div", { style: { padding: 28, height: "100%", overflow: "auto", background: "#f7f8fa" } }, h("div", { style: { maxWidth: 1000, margin: "0 auto" } },
      h("h2", null, "Order Studio"), h("p", { style: { color: "#667085" } }, "解析客户订单，人工核对后写入统一数据库。"),
      h(antd.Input.TextArea, { value: text, rows: 7, onChange: function (e) { setText(e.target.value); }, placeholder: "输入订单号、下单日期、客户、产品、数量和交期" }),
      h(antd.Button, { type: "primary", loading: loading, onClick: run, style: { marginTop: 12 } }, "解析订单"),
      result ? h(React.Fragment, null,
        h(antd.Alert, { style: { marginTop: 16 }, type: result.ready_for_review ? "success" : "warning", showIcon: true, message: result.ready_for_review ? "关键字段已提取，请人工确认" : "订单信息不完整，请在表单中补充", description: "系统不会自动提交，只有点击确认后才会写入真实订单数据。" }),
        h(antd.Card, { title: "标准工单确认", style: { marginTop: 16 }, extra: h(antd.Button, { type: "primary", loading: loading, onClick: confirm }, "确认并写入数据库") },
          h("div", { style: { display: "grid", gridTemplateColumns: "repeat(2,minmax(260px,1fr))", gap: 12 } }, fields.map(function (item) {
            var name = item[0];
            return h("div", { key: name }, h("div", { style: { marginBottom: 5, fontWeight: 600 } }, item[1], item[2] ? " *" : ""),
              name === "status" ? h(antd.Select, { value: draft[name], style: { width: "100%" }, options: ["待排产", "生产中", "待发货", "运输中", "已完成"].map(function (value) { return { value: value, label: value }; }), onChange: function (value) { update(name, value); } })
                : h(antd.Input, { type: name === "quantity" || name === "progress" ? "number" : "text", value: draft[name] == null ? "" : draft[name], onChange: function (e) { update(name, e.target.value); } })
            );
          }))
        ),
        h(antd.Card, { title: "提取证据", style: { marginTop: 16 } }, h(antd.List, { dataSource: result.evidence, renderItem: function (item) { return h(antd.List.Item, null, h(antd.Tag, null, evidenceLabels[item.field] || item.field), item.source); } }))
      ) : null
    ));
  }
  Q.registerRoutes("zhiyun-order-studio", [{ path: "/apps/zhiyun-order-studio", component: OrderStudio, label: "Order Studio", icon: "📋", priority: 88 }]);
})();
