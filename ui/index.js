(function () {
  var Q = window.QwenPaw;
  if (!Q || !Q.host || !Q.host.React || !Q.registerRoutes) return;
  var React = Q.host.React, antd = Q.host.antd, h = React.createElement;

  function request(path, body, method) {
    return Q.host.fetch(path, { method: method || "POST", headers: { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) }).then(function (response) {
      return response.json().then(function (data) { if (!response.ok) throw new Error(data.detail || "操作失败"); return data; });
    });
  }

  function OrderStudio() {
    var textState = React.useState("");
    var text = textState[0], setText = textState[1];
    var resultState = React.useState(null), result = resultState[0], setResult = resultState[1];
    var templateState = React.useState(null), templateResult = templateState[0], setTemplateResult = templateState[1];
    var contractTextState = React.useState(""), contractText = contractTextState[0], setContractText = contractTextState[1];
    var contractState = React.useState(null), contractResult = contractState[0], setContractResult = contractState[1];
    var compareState = React.useState(null), compareResult = compareState[0], setCompareResult = compareState[1];
    var positionState = React.useState("采购方"), userPosition = positionState[0], setUserPosition = positionState[1];
    var draftState = React.useState({}), draft = draftState[0], setDraft = draftState[1];
    var loadingState = React.useState(false), loading = loadingState[0], setLoading = loadingState[1];
    var projectState = React.useState(null), project = projectState[0], setProject = projectState[1];
    var channelState = React.useState("wechat"), channel = channelState[0], setChannel = channelState[1];
    var reviewerState = React.useState(""), reviewer = reviewerState[0], setReviewer = reviewerState[1];
    var message = antd.App.useApp().message;
    var fields = [
      ["order_no", "订单编号", true], ["order_date", "下单日期", true], ["customer_name", "客户名称", true],
      ["product_name", "产品名称", true], ["quantity", "数量", true], ["promised_date", "承诺交期", true],
      ["status", "订单状态", true], ["progress", "完成进度", true]
    ];
    function run() {
      if (!text.trim()) { message.warning("请输入真实的客户订单原文"); return; }
      setLoading(true);
      request("/zhiyun-order-studio/projects", { source_text: text, source_channel: channel }).then(function (saved) {
        setProject(saved);
        var data = saved.runs[0].artifacts.length ? saved.runs[0].artifacts[0].content : null;
        if (!data) throw new Error(saved.runs[0].error_message || "解析失败");
        setResult(data);
        setDraft(Object.assign({}, data.order, { status: data.order.status || "待排产", progress: data.order.progress == null ? 0 : data.order.progress }));
        return request("/zhiyun-order-studio/templates/match", { text: text });
      }).then(setTemplateResult).catch(function (e) { message.error(e.message); }).finally(function () { setLoading(false); });
    }
    function update(name, value) { var next = Object.assign({}, draft); next[name] = value; setDraft(next); }
    function reviewContract() {
      setLoading(true);
      request("/zhiyun-order-studio/contracts/review", { text: contractText, user_position: userPosition })
        .then(function (data) { setContractResult(data); })
        .catch(function (e) { message.error(e.message); })
        .finally(function () { setLoading(false); });
    }
    function importContractFile(file) {
      if (!file) return;
      var reader = new FileReader();
      reader.onload = function () {
        var encoded = String(reader.result).split(",")[1];
        setLoading(true);
        request("/zhiyun-order-studio/contracts/extract-file", { filename: file.name, content_base64: encoded })
          .then(function (data) { setContractText(data.text); setContractResult(null); setCompareResult(null); message.success("已提取 " + data.characters + " 个字符"); })
          .catch(function (e) { message.error(e.message); })
          .finally(function () { setLoading(false); });
      };
      reader.readAsDataURL(file);
    }
    function compareContract() {
      setLoading(true);
      request("/zhiyun-order-studio/contracts/compare-order", { order_text: text, contract_text: contractText })
        .then(function (data) { setCompareResult(data); })
        .catch(function (e) { message.error(e.message); })
        .finally(function () { setLoading(false); });
    }
    function confirm() {
      var missing = fields.filter(function (item) { return item[2] && (draft[item[0]] === null || draft[item[0]] === undefined || draft[item[0]] === ""); });
      if (missing.length) { message.warning("请补齐：" + missing.map(function (item) { return item[1]; }).join("、")); return; }
      if (!reviewer.trim()) { message.warning("请输入审阅人"); return; }
      setLoading(true);
      request("/zhiyun-order-studio/projects/" + project.id + "/reviews", { action: "accept", reviewer: reviewer, order: draft })
        .then(function (saved) { setProject(saved); message.success("审阅已接受，可以导出"); })
        .catch(function (e) { message.error(e.message); }).finally(function () { setLoading(false); });
    }
    function revoke() {
      request("/zhiyun-order-studio/projects/" + project.id + "/reviews", { action: "revoke", reviewer: reviewer || "当前用户" })
        .then(function (saved) { setProject(saved); message.success("已撤销接受"); }).catch(function (e) { message.error(e.message); });
    }
    function exportOrder(format) { window.open("/zhiyun-order-studio/projects/" + project.id + "/export?format=" + format, "_blank"); }
    var evidenceLabels = { order_no: "订单编号", order_date: "下单日期", customer_name: "客户名称", product_name: "产品名称", quantity: "数量", promised_date: "承诺交期" };
    return h("div", { style: { padding: 28, height: "100%", overflow: "auto", background: "#f7f8fa" } }, h("div", { style: { maxWidth: 1000, margin: "0 auto" } },
      h("h2", null, "Order Studio"), h("p", { style: { color: "#667085" } }, "解析客户订单，人工核对后写入统一数据库。"),
      h(antd.Select, { value: channel, onChange: setChannel, style: { width: 180, marginBottom: 10 }, options: [{value:"wechat",label:"微信"},{value:"email",label:"邮件"},{value:"ocr",label:"OCR结果"}] }),
      h(antd.Input.TextArea, { value: text, rows: 7, onChange: function (e) { setText(e.target.value); }, placeholder: "粘贴用户提供的真实微信、邮件或OCR结果文本（不会使用示例订单）" }),
      h(antd.Button, { type: "primary", loading: loading, onClick: run, style: { marginTop: 12 } }, "解析订单"),
      result ? h(React.Fragment, null,
        h(antd.Alert, { style: { marginTop: 16 }, type: result.ready_for_review ? "success" : "warning", showIcon: true, message: result.ready_for_review ? "关键字段已提取，请人工确认" : "订单信息不完整，请在表单中补充", description: "系统不会自动提交，只有点击确认后才会写入真实订单数据。" }),
        templateResult ? h(antd.Card, { title: "推荐处理模板", style: { marginTop: 16 }, extra: h(antd.Tag, { color: templateResult.confidence === "high" ? "green" : "blue" }, "置信度 " + templateResult.confidence) },
          h("div", { style: { display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" } },
            h("strong", { style: { fontSize: 18 } }, templateResult.template.name),
            h(antd.Tag, { color: "geekblue" }, "匹配分 " + templateResult.template.score)
          ),
          h("p", { style: { color: "#667085", marginTop: 8 } }, templateResult.reason),
          h("div", { style: { marginTop: 12, fontWeight: 600 } }, "需要补齐的信息"),
          h("div", { style: { marginTop: 8 } }, templateResult.template.required_fields.map(function (field) { return h(antd.Tag, { key: field, style: { marginBottom: 6 } }, field); })),
          h("div", { style: { marginTop: 12, fontWeight: 600 } }, "建议处理路径"),
          h(antd.Steps, { direction: "vertical", size: "small", current: -1, style: { marginTop: 10 }, items: templateResult.template.process_steps.map(function (step) { return { title: step }; }) }),
          h(antd.Alert, { type: "warning", showIcon: true, message: "模板和处理路径仅为推荐，须由业务人员确认后执行。" })
        ) : null,
        h(antd.Card, { title: "标准工单确认", style: { marginTop: 16 }, extra: h("span", null, project ? h(antd.Tag, null, project.status) : null) },
          h("div", { style: { display: "grid", gridTemplateColumns: "repeat(2,minmax(260px,1fr))", gap: 12 } }, fields.map(function (item) {
            var name = item[0];
            return h("div", { key: name }, h("div", { style: { marginBottom: 5, fontWeight: 600 } }, item[1], item[2] ? " *" : ""),
              name === "status" ? h(antd.Select, { value: draft[name], style: { width: "100%" }, options: ["待排产", "生产中", "待发货", "运输中", "已完成"].map(function (value) { return { value: value, label: value }; }), onChange: function (value) { update(name, value); } })
                : h(antd.Input, { type: name === "quantity" || name === "progress" ? "number" : "text", value: draft[name] == null ? "" : draft[name], onChange: function (e) { update(name, e.target.value); } })
            );
          })),
          h("div", { style: { display:"flex", gap:8, marginTop:14 } },
            h(antd.Input, { value:reviewer, onChange:function(e){setReviewer(e.target.value);}, placeholder:"审阅人", style:{width:180} }),
            h(antd.Button, { type:"primary", loading:loading, onClick:confirm, disabled:project && project.status === "accepted" }, "接受"),
            h(antd.Button, { onClick:revoke, disabled:!project || project.status !== "accepted" }, "撤销"),
            h(antd.Button, { onClick:function(){exportOrder("json");}, disabled:!project || project.status !== "accepted" }, "导出 JSON"),
            h(antd.Button, { onClick:function(){exportOrder("csv");}, disabled:!project || project.status !== "accepted" }, "导出 CSV")
          )
        ),
        h(antd.Card, { title: "提取证据", style: { marginTop: 16 } }, h(antd.List, { dataSource: result.evidence, renderItem: function (item) { return h(antd.List.Item, null, h(antd.Tag, null, evidenceLabels[item.field] || item.field), item.source); } }))
      ) : null,
      h(antd.Card, { title: "合同要素提取与风险初筛", style: { marginTop: 20 } },
        h("div", { style: { display: "flex", gap: 12, marginBottom: 12, alignItems: "center" } },
          h("span", null, "我方身份"),
          h(antd.Select, { value: userPosition, style: { width: 150 }, options: ["采购方", "供应方"].map(function (value) { return { value: value, label: value }; }), onChange: setUserPosition })
        ),
        h(antd.Input.TextArea, { value: contractText, rows: 7, onChange: function (e) { setContractText(e.target.value); }, placeholder: "粘贴合同文本；PDF/Word可先在工作区文件中提取文本" }),
        h("div", { style: { display: "flex", gap: 10, marginTop: 12, flexWrap: "wrap" } },
          h(antd.Button, { type: "primary", loading: loading, onClick: reviewContract }, "提取并检查风险"),
          h(antd.Button, { loading: loading, onClick: compareContract }, "与上方订单核对"),
          h("label", { style: { display: "inline-flex", alignItems: "center", padding: "4px 15px", border: "1px solid #d9d9d9", borderRadius: 6, cursor: "pointer", background: "#fff" } }, "导入合同文件",
            h("input", { type: "file", accept: ".txt,.md,.docx,.pdf", style: { display: "none" }, onChange: function (e) { importContractFile(e.target.files[0]); e.target.value = ""; } })
          )
        ),
        contractResult ? h(React.Fragment, null,
          h(antd.Alert, { style: { marginTop: 16 }, showIcon: true, type: contractResult.overall_risk === "high" ? "error" : contractResult.overall_risk === "medium" ? "warning" : "success", message: "总体风险：" + contractResult.overall_risk, description: contractResult.disclaimer }),
          h(antd.Descriptions, { bordered: true, size: "small", column: 2, style: { marginTop: 16 }, items: [
            ["contract_no", "合同编号"], ["party_a", "甲方/买方"], ["party_b", "乙方/卖方"], ["amount", "合同金额"],
            ["payment_terms", "付款条款"], ["delivery_terms", "交付条件"], ["breach_terms", "违约责任"], ["governing_law", "争议解决"]
          ].map(function (item) { return { key: item[0], label: item[1], children: contractResult.contract[item[0]] || h(antd.Tag, { color: "red" }, "未提取") }; }) }),
          contractResult.missing_clauses.length ? h(antd.Alert, { style: { marginTop: 16 }, type: "warning", showIcon: true, message: "缺失条款：" + contractResult.missing_clauses.join("、") }) : null,
          h(antd.List, { style: { marginTop: 12 }, header: h("strong", null, "风险清单与修改建议"), dataSource: contractResult.findings, locale: { emptyText: "未命中当前规则库中的明显风险，仍需人工复核" }, renderItem: function (item) {
            var color = item.level === "high" ? "red" : item.level === "medium" ? "orange" : "green";
            return h(antd.List.Item, null, h("div", null,
              h(antd.Tag, { color: color }, item.level.toUpperCase()), h("strong", null, item.category + "：" + item.issue),
              h("div", { style: { color: "#667085", marginTop: 6 } }, "原文/依据：" + item.evidence),
              h("div", { style: { marginTop: 4 } }, "建议：" + item.suggestion)
            ));
          } })
        ) : null,
        compareResult ? h(antd.Card, { size: "small", title: "订单—合同一致性验证", style: { marginTop: 16 } },
          h(antd.Alert, { showIcon: true, type: compareResult.consistent ? "success" : "error", message: compareResult.consistent ? "已比较字段未发现差异" : compareResult.summary, description: "比较结果不会自动修改订单或合同，所有差异必须由业务人员确认。" }),
          h(antd.List, { style: { marginTop: 10 }, dataSource: compareResult.differences, locale: { emptyText: "无已确认差异" }, renderItem: function (item) {
            return h(antd.List.Item, null, h(antd.Tag, { color: "red" }, item.field), "订单：" + item.order_value + "；合同：" + item.contract_value);
          } }),
          compareResult.unavailable_fields.length ? h(antd.Collapse, { items: [{ key: "missing", label: "无法比较的字段（" + compareResult.unavailable_fields.length + "）", children: h(antd.List, { size: "small", dataSource: compareResult.unavailable_fields, renderItem: function (item) { return h(antd.List.Item, null, item.field + "：" + item.reason); } }) }] }) : null
        ) : null
      )
    ));
  }
  Q.registerRoutes("zhiyun-order-studio", [{ path: "/apps/zhiyun-order-studio", component: OrderStudio, label: "Order Studio", icon: "📋", priority: 88 }]);
})();
