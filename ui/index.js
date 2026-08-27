(function () {
  var Q = window.QwenPaw;
  if (!Q || !Q.host || !Q.host.React || !Q.registerRoutes) return;
  var React = Q.host.React, antd = Q.host.antd, h = React.createElement;

  function authHeaders() {
    try { var t = window.localStorage.getItem("zhiyun_token"); return t ? { Authorization: "Bearer " + t } : {}; } catch (e) { return {}; }
  }
  function syncToDataCore(order) {
    /* 跨应用数据契约（PRD §9/§19.11）：接受的订单同步统一数据中心 orders 实体，
       Data Studio 的看板即读取同一份记录。失败不阻断审阅流程，仅提示。 */
    var keys = ["order_no", "customer_name", "product_name", "quantity", "order_date", "promised_date", "status", "progress"];
    var row = {};
    keys.forEach(function (k) { if (order[k] !== null && order[k] !== undefined && order[k] !== "") row[k] = order[k]; });
    if (!row.order_no || !row.customer_name) return;
    Q.host.fetch("/zhiyun-data-core/imports/orders/commit?data_mode=production", {
      method: "POST",
      headers: Object.assign({ "Content-Type": "application/json" }, authHeaders()),
      body: JSON.stringify({ rows: [row], source_name: "order-studio-" + (project && project.id ? project.id : "order") })
    }).then(function (response) {
      if (!response.ok) throw new Error("HTTP " + response.status);
      return response.json();
    }).then(function (batch) {
      message.success("订单已同步统一数据中心（正式批次，Data Studio 可读）");
    }).catch(function (e) {
      message.warning("审阅已接受；同步数据中心未完成：" + (e.message || "未知原因"));
    });
  }
  function request(path, body, method) {
    return Q.host.fetch(path, { method: method || "POST", headers: Object.assign({ "Content-Type": "application/json" }, authHeaders()), body: body === undefined ? undefined : JSON.stringify(body) }).then(function (response) {
      return response.json().then(function (data) { if (!response.ok) throw new Error(data.detail || "操作失败"); return data; });
    });
  }


  function zyPushAgent(ctx) {
    if (Q.setAgentContext) Q.setAgentContext(ctx);
    else window.dispatchEvent(new CustomEvent("qwenpaw:agent-context", { detail: ctx }));
  }
  function zySpark() { return h("span", { style: { fontSize: 13 } }, "✦"); }
  function AgentDock(props) {
    var listRef = React.useRef(null);
    React.useEffect(function () {
      if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
    }, [props.messages]);
    if (!props.open) return null;
    var S = {
      mask: { position: "fixed", inset: 0, background: "rgba(15,23,42,0.32)", zIndex: 1000 },
      dock: { position: "fixed", top: 0, right: 0, bottom: 0, width: "min(420px,92vw)", background: "#ffffff", borderLeft: "1px solid #e3e8ef", boxShadow: "-10px 0 30px rgba(16,24,40,0.16)", zIndex: 1001, display: "flex", flexDirection: "column" },
      chat: { display: "flex", flexDirection: "column", height: "100%" },
      head: { padding: "14px 16px", background: "#ffffff", borderBottom: "1px solid #e3e8ef" },
      close: { border: "none", background: "transparent", cursor: "pointer", fontSize: 18, lineHeight: 1, color: "#98a2b3", padding: "4px 8px", borderRadius: 6 },
      list: { flex: "1 1 auto", overflow: "auto", padding: 16 },
      msg: { display: "flex", flexDirection: "column", gap: 6, marginBottom: 14 },
      bubble: { maxWidth: "92%", padding: "10px 12px", borderRadius: 11, fontSize: "12.5px", lineHeight: 1.6, boxShadow: "0 1px 2px rgba(16,24,40,0.04)", whiteSpace: "pre-wrap" },
      card: { maxWidth: "92%", background: "#ffffff", border: "1px solid #e3e8ef", borderRadius: 11, padding: "12px 14px", boxShadow: "0 1px 2px rgba(16,24,40,0.04)", fontSize: 12.5 },
      input: { padding: "12px 14px", background: "#ffffff", borderTop: "1px solid #e3e8ef" },
      chips: { display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 },
      chip: { border: "1px solid #e3e8ef", background: "#ffffff", borderRadius: 999, padding: "6px 12px", fontSize: 12, color: "#5b6472", cursor: "pointer" }
    };
    return h("div", null,
      h("div", { style: S.mask, onClick: props.onClose }),
      h("div", { style: S.dock },
        h("div", { style: S.chat },
          h("div", { style: S.head },
            h("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 } },
              h("span", { style: { fontWeight: 650, fontSize: 15, color: "#1f2933" } }, "智能体助手 · " + (props.moduleLabel || "")),
              h("button", { "aria-label": "关闭", onClick: props.onClose, style: S.close }, "✕")
            ),
            h("div", { style: { fontSize: 12, color: "#5b6472", marginTop: 8, lineHeight: 1.5 } }, "直接打字告诉我要做什么，或点击下方快捷指令，自动载入示例并交给智能体处理。"),
            h("div", { style: S.chips },
              (props.chips || []).map(function (c) {
                return h("span", { key: c.key, style: S.chip, onClick: function () { props.onCommand(c.key, c.label); } }, c.label);
              })
            )
          ),
          h("div", { style: S.list, ref: listRef },
            (props.messages || []).map(function (msg, i) {
              var user = msg.role === "user";
              return h("div", { key: i, style: Object.assign({}, S.msg, user ? { alignItems: "flex-end" } : { alignItems: "flex-start" }) },
                h("div", { style: Object.assign({}, S.bubble, user ? { background: "#2563eb", color: "#fff", borderBottomRightRadius: 3 } : { background: "#ffffff", border: "1px solid #e3e8ef", color: "#1f2933", borderBottomLeftRadius: 3 }) }, msg.text),
                msg.card ? h("div", { style: S.card }, msg.card) : null
              );
            })
          ),
          h("div", { style: S.input },
            h(antd.Input, { value: props.draft, placeholder: props.placeholder || "例如：帮我分析当前风险", onChange: function (e) { props.setDraft(e.target.value); }, onPressEnter: function (e) { if (props.draft.trim()) { props.onSend(props.draft); e.preventDefault(); } } }),
            h(antd.Button, { type: "primary", style: { marginTop: 10, width: "100%" }, loading: props.busy, onClick: function () { if (props.draft.trim()) props.onSend(props.draft); } }, "发送")
          )
        )
      )
    );
  }

  function OrderStudio() {
    var textState = React.useState("");
    var text = textState[0], setText = textState[1];
    var resultState = React.useState(null), result = resultState[0], setResult = resultState[1];
    var templateState = React.useState(null), templateResult = templateState[0], setTemplateResult = templateState[1];
    var contractTextState = React.useState(""), contractText = contractTextState[0], setContractText = contractTextState[1];
    var contractState = React.useState(null), contractResult = contractState[0], setContractResult = contractState[1];
    var compareState = React.useState(null), compareResult = compareState[0], setCompareResult = compareState[1];
    var exceptionState = React.useState(null), exceptionCase = exceptionState[0], setExceptionCase = exceptionState[1];
    var exceptionPathState = React.useState(""), exceptionPath = exceptionPathState[0], setExceptionPath = exceptionPathState[1];
    var exceptionWordingState = React.useState(""), exceptionWording = exceptionWordingState[0], setExceptionWording = exceptionWordingState[1];
    var positionState = React.useState("采购方"), userPosition = positionState[0], setUserPosition = positionState[1];
    var draftState = React.useState({}), draft = draftState[0], setDraft = draftState[1];
    var loadingState = React.useState(false), loading = loadingState[0], setLoading = loadingState[1];
    var projectState = React.useState(null), project = projectState[0], setProject = projectState[1];
    var channelState = React.useState("wechat"), channel = channelState[0], setChannel = channelState[1];
    var orderSimulationState = React.useState(false), orderIsSimulation = orderSimulationState[0], setOrderIsSimulation = orderSimulationState[1];
    var contractSimulationState = React.useState(false), contractIsSimulation = contractSimulationState[0], setContractIsSimulation = contractSimulationState[1];
    var reviewerState = React.useState(""), reviewer = reviewerState[0], setReviewer = reviewerState[1];
    var message = antd.App.useApp().message;
    var agentOpenState = React.useState(false), agentOpen = agentOpenState[0], setAgentOpen = agentOpenState[1];
    var agentDraftState = React.useState(""), agentDraft = agentDraftState[0], setAgentDraft = agentDraftState[1];
    var agentMsgState = React.useState([]), agentMessages = agentMsgState[0], setAgentMessages = agentMsgState[1];
    var agentBusyState = React.useState(false), agentBusy = agentBusyState[0], setAgentBusy = agentBusyState[1];
    var agentSummary = function () { return result || contractResult || exceptionCase || null; };

    function agentAdd(role, text, card) {
      setAgentMessages(function (prev) { return prev.concat([{ role: role, text: text, card: card }]); });
    }
    function agentCommand(key, label) {
      var usesSimulation = false;
      if (key === "parse" && !text.trim()) {
        setText("客户反馈订单：A202608001，采购伺服电机 5 台，单价 6800 元，承诺 2026-09-15 前交付，联系人张工，电话 13800001234。");
        setOrderIsSimulation(true);
        usesSimulation = true;
      }
      if (key === "contract" && !contractText.trim()) {
        setContractText("采购合同\n合同编号 HT-2026-088\n甲方（买方）：广州智云\n乙方（卖方）：东莞市某电机公司\n合同金额：人民币 34000 元\n付款条件：预付 30%，货到后 30 日内付清剩余 70%\n交付地点：甲方工厂\n违约条款：延迟交付每日按 0.5% 计算违约金");
        setContractIsSimulation(true);
        usesSimulation = true;
      }
      usesSimulation = usesSimulation || (key === "parse" && orderIsSimulation) || (key === "contract" && contractIsSimulation) || (key === "exception" && (orderIsSimulation || contractIsSimulation));
      agentAdd("user", label || key);
      setAgentBusy(true);
      setTimeout(function () {
        zyPushAgent({ app_id: "zhiyun-order-studio", kind: key, label: label || key, summary: agentSummary(), source_type: usesSimulation ? "simulated" : "real" });
        setAgentBusy(false);
        agentAdd("bot", "已定位至「" + (label || key) + "」，示例已载入，可直接在界面运行并生成可审阅处理建议。", null);
      }, 250);
    }
    function agentSend(text) {
      agentAdd("user", text);
      setAgentBusy(true);
      var key = /合同|风险|条款|差异/.test(text) ? "contract" : /异常|方案|分歧|争议/.test(text) ? "exception" : "parse";
      setTimeout(function () {
        var simulated = key === "parse" ? orderIsSimulation : key === "contract" ? contractIsSimulation : (orderIsSimulation || contractIsSimulation);
        zyPushAgent({ app_id: "zhiyun-order-studio", kind: key, label: text, summary: agentSummary(), source_type: simulated ? "simulated" : "real" });
        setAgentBusy(false);
        agentAdd("bot", "已将问题交给订单智能体，前往「" + (key === "contract" ? "合同要素提取与风险初筛" : key === "exception" ? "异常处理工作台" : "标准工单确认") + "」查看处理建议。", null);
      }, 250);
    }

    var fields = [
      ["order_no", "订单编号", true], ["order_date", "下单日期", true], ["customer_name", "客户名称", true],
      ["product_name", "产品名称", true], ["quantity", "数量", true], ["promised_date", "承诺交期", true],
      ["status", "订单状态", true], ["progress", "完成进度", true]
    ];
    function run(overrideText, overrideChannel) {
      var src = overrideText !== undefined ? overrideText : text;
      var selectedChannel = overrideChannel || channel;
      if (!src.trim()) { message.warning("请输入真实的客户订单原文"); return; }
      setLoading(true);
      return request("/zhiyun-order-studio/projects", { source_text: src, source_channel: selectedChannel }).then(function (saved) {
        setProject(saved);
        setOrderIsSimulation(selectedChannel === "simulation");
        var data = saved.runs[0].artifacts.length ? saved.runs[0].artifacts[0].content : null;
        if (!data) throw new Error(saved.runs[0].error_message || "解析失败");
        setResult(data);
        setDraft(Object.assign({}, data.order, { status: data.order.status || "待排产", progress: data.order.progress == null ? 0 : data.order.progress }));
        return request("/zhiyun-order-studio/templates/match", { text: src }).then(function (matched) {
          setTemplateResult(matched);
          return saved;
        });
      }).catch(function (e) { message.error(e.message); return null; }).finally(function () { setLoading(false); });
    }
    function update(name, value) { var next = Object.assign({}, draft); next[name] = value; setDraft(next); }
    function reviewContract(overrideText) {
      var contract = overrideText !== undefined ? overrideText : contractText;
      if (!contract.trim()) { message.warning("请输入合同文本"); return; }
      setLoading(true);
      request("/zhiyun-order-studio/contracts/review", { text: contract, user_position: userPosition })
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
          .then(function (data) { setContractText(data.text); setContractIsSimulation(false); setContractResult(null); setCompareResult(null); message.success("已提取 " + data.characters + " 个字符"); })
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
    function createException(overrideOrder, overrideContract, overrideProjectId) {
      var o = overrideOrder !== undefined ? overrideOrder : text;
      var c = overrideContract !== undefined ? overrideContract : contractText;
      if (!o.trim() || !c.trim()) { message.warning("请先填写订单和合同原文"); return; }
      setLoading(true);
      return request("/zhiyun-order-studio/exceptions", { order_text: o, contract_text: c, project_id: overrideProjectId !== undefined ? overrideProjectId : (project ? project.id : null) })
        .then(function (data) {
          setExceptionCase(data);
          var first = data.recommendation.recommendations[0];
          setExceptionPath(first ? first.handling_path.join(" → ") : "");
          setExceptionWording(first ? first.suggested_wording : "");
        }).catch(function (e) { message.error(e.message); }).finally(function () { setLoading(false); });
    }
    function decideException(action) {
      if (!reviewer.trim()) { message.warning("请输入审阅人"); return; }
      request("/zhiyun-order-studio/exceptions/" + exceptionCase.id + "/reviews", {
        action: action, reviewer: reviewer, selected_path: exceptionPath, wording: exceptionWording
      }).then(function (data) { setExceptionCase(data); message.success(action === "accept" ? "异常方案已接受" : "异常方案已驳回"); })
        .catch(function (e) { message.error(e.message); });
    }
    function retryException() {
      request("/zhiyun-order-studio/exceptions/" + exceptionCase.id + "/retry", {})
        .then(function (data) { setExceptionCase(data); message.success("已根据原始证据重新生成建议"); })
        .catch(function (e) { message.error(e.message); });
    }
    function confirm() {
      var missing = fields.filter(function (item) { return item[2] && (draft[item[0]] === null || draft[item[0]] === undefined || draft[item[0]] === ""); });
      if (missing.length) { message.warning("请补齐：" + missing.map(function (item) { return item[1]; }).join("、")); return; }
      if (!reviewer.trim()) { message.warning("请输入审阅人"); return; }
      setLoading(true);
      request("/zhiyun-order-studio/projects/" + project.id + "/reviews", { action: "accept", reviewer: reviewer, order: draft })
        .then(function (saved) { setProject(saved); message.success("审阅已接受，可以导出"); syncToDataCore(draft); })
        .catch(function (e) { message.error(e.message); }).finally(function () { setLoading(false); });
    }
    function revoke() {
      request("/zhiyun-order-studio/projects/" + project.id + "/reviews", { action: "revoke", reviewer: reviewer || "当前用户" })
        .then(function (saved) { setProject(saved); message.success("已撤销接受"); }).catch(function (e) { message.error(e.message); });
    }
    function exportOrder(format) { window.open("/zhiyun-order-studio/projects/" + project.id + "/export?format=" + format, "_blank"); }
    var evidenceLabels = { order_no: "订单编号", order_date: "下单日期", customer_name: "客户名称", product_name: "产品名称", quantity: "数量", promised_date: "承诺交期" };
    var sampleOrder = "客户反馈订单：A202608001，采购伺服电机 5 台，单价 6800 元，承诺 2026-09-15 前交付，联系人张工，电话 13800001234。";
    var sampleContract = "采购合同\n合同编号 HT-2026-088\n甲方（买方）：广州智云\n乙方（卖方）：东莞市某电机公司\n合同金额：人民币 34000 元\n付款条件：预付 30%，货到后 30 日内付清剩余 70%\n交付地点：甲方工厂\n违约条款：延迟交付每日按 0.5% 计算违约金";
    function loadOrderExample() {
      setText(sampleOrder);
      setOrderIsSimulation(true);
      message.success("已载入模拟示例订单，点击「解析订单」即可生成结果");
    }
    function loadContractExample() {
      setContractText(sampleContract);
      setContractIsSimulation(true);
      message.success("已载入模拟示例合同，点击「提取并检查风险」即可生成结果");
    }
    return h("div", { style: { padding: 28, height: "100%", overflow: "auto", background: "#f7f8fa" } }, h("div", { style: { maxWidth: 1000, margin: "0 auto" } },
      h("h2", null, "智能订单中心"), h("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 } }, h("div", null, h("h2", { style: { margin: 0 } }, "智能订单中心"), h("p", { style: { color: "#667085", marginTop: 6 } }, "解析客户订单和合同，人工核对后写入统一数据库。")), h(antd.Button, { type: "primary", onClick: function () { setAgentOpen(true); } }, zySpark(), " 问 Agent")),
      h(antd.Collapse, { style: { marginBottom: 14 }, items: [{ key: "guide", label: "功能引导与使用说明", children: h("div", null,
        h("p", null, "功能介绍：从微信、邮件或 OCR 原文提取标准订单，检查合同风险和订单合同差异，并生成可审阅的异常处理方案。"),
        h("ol", null, h("li", null, "选择来源并粘贴真实订单原文，或点击「载入示例」快速体验。"), h("li", null, "点击解析订单时，原文和运行证据会立即保存到当前工作区，便于恢复和审计。"), h("li", null, "补齐缺失字段并填写审阅人；只有接受后，标准订单才会写入统一数据中心。"), h("li", null, "合同可直接粘贴、上传 PDF/Word/Markdown/TXT，或点击「载入示例」直接体验。")),
        h(antd.Alert, { type: "warning", showIcon: true, message: "合同风险结果是业务初筛，不构成法律意见；系统不会自动提交或修改原件。" })) }] }),
      h(antd.Select, { value: channel, onChange: setChannel, style: { width: 180, marginBottom: 10 }, options: [{value:"wechat",label:"微信"},{value:"email",label:"邮件"},{value:"ocr",label:"OCR结果"}] }),
      h(antd.Input.TextArea, { value: text, rows: 7, onChange: function (e) { setText(e.target.value); setOrderIsSimulation(false); }, placeholder: "粘贴用户提供的真实微信、邮件或OCR结果文本；也可点击「载入示例」快速尝试" }),
      h("div", { style: { display: "flex", gap: 10, marginTop: 12 } },
        h(antd.Button, { type: "primary", loading: loading, onClick: function () { run(); } }, "解析订单"),
        h(antd.Button, { onClick: loadOrderExample }, "载入模拟示例"),
        h(antd.Button, { type: "primary", loading: loading, onClick: function () { loadOrderExample(); run(sampleOrder, "simulation"); } }, "载入模拟示例并运行")
      ),
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
        h(antd.Input.TextArea, { value: contractText, rows: 7, onChange: function (e) { setContractText(e.target.value); setContractIsSimulation(false); }, placeholder: "粘贴合同文本；PDF/Word可先在工作区文件中提取文本；也可点击「载入示例」快速尝试" }),
        h("div", { style: { display: "flex", gap: 10, marginTop: 12, flexWrap: "wrap" } },
          h(antd.Button, { type: "primary", loading: loading, onClick: function () { reviewContract(); } }, "提取并检查风险"),
          h(antd.Button, { onClick: loadContractExample }, "载入模拟示例合同"),
          h(antd.Button, { type: "primary", loading: loading, onClick: function () { loadContractExample(); reviewContract(sampleContract); } }, "载入模拟示例并检查"),
          h(antd.Button, { loading: loading, onClick: compareContract }, "与上方订单核对"),
          h(antd.Button, { danger: true, loading: loading, onClick: function () { createException(); } }, "创建异常处理方案"),
          h(antd.Button, { danger: true, loading: loading, onClick: function () { loadOrderExample(); loadContractExample(); run(sampleOrder, "simulation").then(function (saved) { return saved ? createException(sampleOrder, sampleContract, saved.id) : null; }); } }, "载入模拟示例并建异常"),
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
        ) : null,
        exceptionCase ? h(antd.Card, { size: "small", title: "异常处理工作台", style: { marginTop: 16 }, extra: h(antd.Tag, { color: exceptionCase.status === "accepted" ? "green" : exceptionCase.status === "rejected" ? "red" : "orange" }, exceptionCase.status) },
          h(antd.Alert, { showIcon: true, type: "warning", message: exceptionCase.recommendation.disclaimer, description: "异常类别：" + (exceptionCase.recommendation.categories.join("、") || "无") }),
          h(antd.List, { style: { marginTop: 12 }, dataSource: exceptionCase.recommendation.recommendations, locale: { emptyText: "当前证据未发现需处理的异常" }, renderItem: function (item) {
            return h(antd.List.Item, null, h("div", { style: { width: "100%" } }, h("strong", null, item.title), h("div", { style: { color: "#667085", marginTop: 4 } }, item.category + " · " + item.handling_path.join(" → ")), h("div", { style: { marginTop: 4 } }, item.suggested_wording)));
          } }),
          exceptionCase.recommendation.similar_resolved_cases.length ? h(antd.Collapse, { items: [{ key: "similar", label: "真实历史相似处理（" + exceptionCase.recommendation.similar_resolved_cases.length + "）", children: h(antd.List, { size: "small", dataSource: exceptionCase.recommendation.similar_resolved_cases, renderItem: function (item) { return h(antd.List.Item, null, item.matched_categories.join("、") + " · " + item.selected_path + " · 审阅人 " + item.reviewer); } }) }] }) : null,
          h("div", { style: { marginTop: 12, display: "grid", gap: 8 } },
            h(antd.Input.TextArea, { value: exceptionPath, rows: 2, onChange: function (e) { setExceptionPath(e.target.value); }, placeholder: "确认或调整处理路径" }),
            h(antd.Input.TextArea, { value: exceptionWording, rows: 3, onChange: function (e) { setExceptionWording(e.target.value); }, placeholder: "确认或调整对外回复话术" }),
            h("div", { style: { display: "flex", gap: 8, flexWrap: "wrap" } },
              h(antd.Button, { type: "primary", disabled: exceptionCase.status === "no_exception", onClick: function () { decideException("accept"); } }, "接受异常方案"),
              h(antd.Button, { danger: true, disabled: exceptionCase.status === "no_exception", onClick: function () { decideException("reject"); } }, "驳回"),
              h(antd.Button, { onClick: retryException }, "重试/恢复"),
              h(antd.Button, { disabled: exceptionCase.status !== "accepted", onClick: function () { window.open("/zhiyun-order-studio/exceptions/" + exceptionCase.id + "/export", "_blank"); } }, "导出异常方案")
            )
          )
        ) : null
      ),
      h(AgentDock, { open: agentOpen, onClose: function () { setAgentOpen(false); }, chips: [{ key: "parse", label: "解析订单" }, { key: "contract", label: "合同风险" }, { key: "exception", label: "异常方案" }], moduleLabel: "智能订单中心", messages: agentMessages, draft: agentDraft, setDraft: setAgentDraft, busy: agentBusy, onSend: agentSend, onCommand: agentCommand })
    ));
  }
  Q.registerRoutes("zhiyun-order-studio", [{ path: "/apps/zhiyun-order-studio", component: OrderStudio, label: "智能订单中心", icon: "📋", priority: 88 }]);
})();
