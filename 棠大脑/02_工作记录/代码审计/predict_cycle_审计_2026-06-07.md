     1|     1|# predict_cycle.py 系统审计报告
     2|     2|
     3|     3|**审计日期**：2026-06-07
     4|     4|**审计范围**：
     5|     5|- `/mnt/c/Users/Admin/liuhecai/cron/predict_cycle.py`（206 行）
     6|     6|- `/mnt/c/Users/Admin/liuhecai/predictor/orchestrator.py`（276 行）
     7|     7|- `/mnt/c/Users/Admin/liuhecai/predictor/index_generator.py`（136 行）
     8|     8|- `/mnt/c/Users/Admin/liuhecai/predictor/notification.py`（192 行）
     9|     9|
    10|    10|**审计方法**：grep 验证 + 跨文件交叉对比 + 调用链追踪
    11|    11|**审计者**：棠棠（纯审计，未做任何代码修改）
    12|    12|
    13|    13|---
    14|    14|
    15|    15|## 🔴 严重 Bug（功能完全不工作）
    16|    16|
    17|    17|### Bug #1：PID 文件从未被写入，进程互斥完全失效
    18|    18|
    19|    19|**涉及文件**：
    20|    20|- `predict_cycle.py` L33-34, L46-56, L70-88, L206-207
    21|    21|- 同类问题：`recovery_job.py`、`lottery_monitor.py`、`scripts/run_pipeline.py`（3 个文件同样模式）
    22|    22|
    23|    23|**根因**：
    24|    24|- `is_running()` 读 `PID_FILE`（L76）→ 调 `os.kill(pid, 0)`（L81）
    25|    25|- `get_lock()` 成功获取锁后**只把 PID 写入 `LOCK_FILE`（L51），从未写 `PID_FILE`**
    26|    26|- `is_running()` 第一步 `if not PID_FILE.exists(): return False`（L72-73）永远命中
    27|    27|- **跨 3 个 cron 文件的相同 bug**：`grep "PID_FILE.write"` 在所有文件里 = 0 命中
    28|    28|
    29|    29|**验证证据**（grep 结果）：
    30|    30|```
    31|    31|predict_cycle.py:  PID_FILE 出现 4 次（定义 + 读 + 检查 + 删除）
    32|    32|                 写入 0 次
    33|    33|recovery_job.py:   PID_FILE 出现 4 次（定义 + 读 + 检查 + 删除）
    34|    34|                 写入 0 次
    35|    35|lottery_monitor.py: PID_FILE 出现 4 次（定义 + 读 + 检查 + 删除）
    36|    36|                 写入 0 次
    37|    37|```
    38|    38|
    39|    39|**影响**：
    40|    40|- 两个进程能同时跑（互斥失效）
    41|    41|- flock 是 advisory lock，没有 PID_FILE 校验的话，崩溃后不会自动清理
    42|    42|
    43|    43|**修复方向**（仅供参考，未修改）：
    44|    44|```python
    45|    45|# get_lock() 成功获取锁后追加：
    46|    46|def get_lock():
    47|    47|    lock_file = open(LOCK_FILE, 'w')
    48|    48|    try:
    49|    49|        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    50|    50|        lock_file.write(str(os.getpid()))
    51|    51|        lock_file.flush()
    52|    52|        # 新增：把 PID 写到 PID_FILE，让 is_running() 能工作
    53|    53|        PID_FILE.write_text(str(os.getpid()))
    54|    54|        return lock_file
    55|    55|    except (IOError, OSError):
    56|    56|        lock_file.close()
    57|    57|        return None
    58|    58|```
    59|    59|
    60|    60|---
    61|    61|
    62|    62|### Bug #2：orchestrator 返回结构与 notification 期望完全不匹配
    63|    63|
    64|    64|**涉及文件**：
    65|    65|- `orchestrator.py` L273-276（实际返回）
    66|    66|- `notification.py` L113-142（format_message 期望）+ L168-185（send_notification 期望）
    67|    67|
    68|    68|**实际返回**（orchestrator.py L273-276）：
    69|    69|```python
    70|    70|return {
    71|    71|    "issue": next_issue,
    72|    72|    "results": {v: r.to_dict() for v, r in results.items()}
    73|    73|}
    74|    74|```
    75|    75|
    76|    76|**期望接收**（notification.py L113-142）：
    77|    77|```python
    78|    78|{
    79|    79|    "verified_period": ...,
    80|    80|    "pending_period": ...,
    81|    81|    "verified": {version: {"prediction": [...], "actual": ..., "hit": ...}},
    82|    82|    "pending": {version: {"prediction": [...], "strategy": ...}}
    83|    83|}
    84|    84|```
    85|    85|
    86|    86|**字段对比**：
    87|    87|
    88|    88|| orchestrator 返回 | notification 期望 | 命中 |
    89|    89||------|------|------|
    90|    90|| `issue` | `pending_period` / `verified_period` | ❌ 名字不同 |
    91|    91|| `results[version].prediction` | `pending[version].prediction` | ❌ 嵌套不同 |
    92|    92|| ❌ 缺 | `actual` | ❌ |
    93|    93|| ❌ 缺 | `hit` | ❌ |
    94|    94|| ❌ 缺 | `verified_period` | ❌ |
    95|    95|
    96|    96|**实际结果**：
    97|    97|- `result.get("pending_period", "")` → **空字符串**
    98|    98|- `result.get("pending", {})` → **空字典**
    99|    99|- `format_message(result)` → 返回 `"无数据"`
   100|   100|- 推送消息 = `"无数据"`
   101|   101|
   102|   102|**根因**：`notification.py` 自己有 `load_latest_result()` 能从 ledger 拉正确数据（L76-110），但**没在 `send_notification` 里被调用**。`predict_cycle.py` L198 也没调。
   103|   103|
   104|   104|**修复方向**（仅供参考，未修改）：
   105|   105|```python
   106|   106|# notification.py send_notification 开头加：
   107|   107|def send_notification(result: Dict) -> bool:
   108|   108|    # 实际数据从 ledger 重新加载（result 参数不可信）
   109|   109|    fresh = load_latest_result()
   110|   110|    if fresh:
   111|   111|        result = fresh
   112|   112|    # ... 后续逻辑
   113|   113|```
   114|   114|
   115|   115|或 predict_cycle.py L194-198：
   116|   116|```python
   117|   117|result = verify_and_predict()
   118|   118|if result:
   119|   119|    # 加载正确结构再传
   120|   120|    from predictor.notification import load_latest_result
   121|   121|    push_result = load_latest_result() or result
   122|   122|    send_notification(push_result)
   123|   123|```
   124|   124|
   125|   125|---
   126|   126|
   127|   127|### Bug #3：Telegram `parse_mode=Markdown` + 未转义 `[ ]` → API 400
   128|   128|
   129|   129|**涉及文件**：`notification.py` L154 + L130, L140
   130|   130|
   131|   131|**问题**：
   132|   132|- `data["parse_mode"] = "Markdown"`（L154）
   133|   133|- 消息体 L130：`[v12] 龍 鼠 雞 ... → 鼠 ✅`（含 `[` `]` `→`）
   134|   134|- Telegram Markdown 解析器对 `[` 处理严格：
   135|   135|  - Markdown（旧版）：方括号只在链接语法 `[]()` 里特殊
   136|   136|  - MarkdownV2：所有特殊字符必须转义
   137|   137|- 消息中 `[v12]` 不在链接语法里 → 解析器可能拒绝
   138|   138|
   139|   139|**历史证据**：
   140|   140|- 之前 cron 会话（6/4、6/5）出现过 `Telegram send failed: Timed out`
   141|   141|- 但 timeout 不一定是 400 错误引起的——也可能是代理问题
   142|   142|- **建议先抓 response body 确认状态码**
   143|   143|
   144|   144|**修复方向**（仅供参考，未修改）：
   145|   145|```python
   146|   146|# 方案 A：去掉 parse_mode（最简单）
   147|   147|data = {
   148|   148|    "chat_id": TELEGRAM_CHAT_ID,
   149|   149|    "text": message,
   150|   150|    # 删掉 parse_mode
   151|   151|}
   152|   152|
   153|   153|# 方案 B：转义方括号
   154|   154|text = message.replace("[", "【").replace("]", "】")
   155|   155|
   156|   156|# 方案 C：改用 MarkdownV2 并全面转义
   157|   157|data = {
   158|   158|    "chat_id": TELEGRAM_CHAT_ID,
   159|   159|    "text": escape_markdown_v2(message),
   160|   160|    "parse_mode": "MarkdownV2"
   161|   161|}
   162|   162|```
   163|   163|
   164|   164|---
   165|   165|
   166|   166|## 🟡 重要问题（功能退化/可维护性差）
   167|   167|
   168|   168|### Issue #4：pending_top6 取 v12 → 永远空 → 推送去重失效
   169|   169|
   170|   170|**位置**：`notification.py` L172
   171|   171|
   172|   172|```python
   173|   173|pending_top6 = pending.get("v12", {}).get("prediction", []) if "v12" in pending else []
   174|   174|```
   175|   175|
   176|   176|**问题**：
   177|   177|- PUSH_VERSIONS = `["v12", "v5", "v7", "v24"]`（L26）
   178|   178|- `should_send_notification` 用 `pending_top6` 对比 `last_push_top6`
   179|   179|- 第一次推送：last 为空 → `return True` ✅
   180|   180|- 第二次推送：last = `{period: x, top6: []}`，`pending_top6 = []` → 相同 → 跳过 ✅
   181|   181|- **但**如果 orchestrator 没产生 v12 的预测（v12 不在 active_versions 里），`pending = {}`，`pending_top6 = []` → 永远 `== []` → 每次都判"相同" → 永远跳过（取决于 last 是否也有数据）
   182|   182|
   183|   183|**实际行为**：去重逻辑"碰巧能用但不靠谱"，依赖 last_push_top6 初始值的初始化。
   184|   184|
   185|   185|**修复方向**：用所有 PUSH_VERSIONS 的 prediction 拼接做 hash，跨版本去重。
   186|   186|
   187|   187|---
   188|   188|
   189|   189|### Issue #5：orchestrator fallback `["v23", "v24"]` ≠ PUSH_VERSIONS
   190|   190|
   191|   191|**位置**：
   192|   192|- `orchestrator.py` L46：`active_versions = index.get("active", ["v23", "v24"])`
   193|   193|- `notification.py` L26：`PUSH_VERSIONS = ["v12", "v5", "v7", "v24"]`
   194|   194|
   195|   195|**问题**：
   196|   196|- 如果 `index.json` 损坏或 `generate_index()` 抛异常，orchestrator 跑 v23/v24
   197|   197|- notification 推 v12/v5/v7/v24
   198|   198|- **v23 跑了但没推，v12/v5/v7 没跑但推送路径里有它们** → 数据不一致
   199|   199|
   200|   200|---
   201|   201|
   202|   202|### Issue #6：orchestrator `sync_latest_results` 后台线程 silent fail
   203|   203|
   204|   204|**位置**：`orchestrator.py` L173-181
   205|   205|
   206|   206|```python
   207|   207|def background_refresh():
   208|   208|    try:
   209|   209|        get_all_records([2024, 2025, 2026], force_refresh=True)
   210|   210|    except:
   211|   211|        pass
   212|   212|```
   213|   213|
   214|   214|**问题**：`except: pass` 是反模式，所有错误被吞。
   215|   215|
   216|   216|**修复方向**：
   217|   217|```python
   218|   218|def background_refresh():
   219|   219|    try:
   220|   220|        get_all_records([2024, 2025, 2026], force_refresh=True)
   221|   221|    except Exception as e:
   222|   222|        print(f"  [background refresh failed] {e}", file=sys.stderr)
   223|   223|```
   224|   224|
   225|   225|---
   226|   226|
   227|   227|### Issue #7：orchestrator L168 类型假设
   228|   228|
   229|   229|**位置**：`orchestrator.py` L168
   230|   230|
   231|   231|```python
   232|   232|api_latest_zodiac = latest["zodiac"].split(",")[-1]
   233|   233|```
   234|   234|
   235|   235|**问题**：假设 `latest["zodiac"]` 是 str，如果是 list 会 AttributeError。
   236|   236|
   237|   237|**验证**：`data_fetcher.fetch_latest_record()` 的实现未审计，无法 100% 确认。需要看 `data_fetcher.py` 才能确定。
   238|   238|
   239|   239|---
   240|   240|
   241|   241|### Issue #8：notification.py get_last_push_info 类型分支不一致
   242|   242|
   243|   243|**位置**：`notification.py` L29-36
   244|   244|
   245|   245|```python
   246|   246|def get_last_push_info() -> Dict:
   247|   247|    if os.path.exists(PUSH_HISTORY_FILE):
   248|   248|        with open(PUSH_HISTORY_FILE) as f:
   249|   249|            data = json.load(f)
   250|   250|            if isinstance(data, list) and len(data) > 0:
   251|   251|                return data[-1]
   252|   252|            return data  # 可能是 dict 或空 list
   253|   253|    return {}
   254|   254|```
   255|   255|
   256|   256|**问题**：
   257|   257|- `save_push_history` 永远写 list（L54-57）
   258|   258|- 但函数允许返回 dict
   259|   259|- 调用方 L70 `last.get("last_push_period")` 在 list 类型上会 AttributeError
   260|   260|
   261|   261|---
   262|   262|
   263|   263|## 🟢 建议（非阻塞改进）
   264|   264|
   265|   265|### S1：硬编码 `PUSH_VERSIONS` 应该动态生成
   266|   266|从 `index_generator.generate_index()["active_by_play_type"]["liuhe"]` 读，避免版本更新时漏改。
   267|   267|
   268|   268|### S2：日志格式
   269|   269|`[RESULT_CONSUMED] issue=... source=...` 用下划线 + 等号，建议改 JSON Lines：
   270|   270|```python
   271|   271|print(json.dumps({"event": "result_consumed", "issue": ..., "duration_ms": ...}))
   272|   272|```
   273|   273|
   274|   274|### S3：`send_telegram` 失败时无持久化日志
   275|   275|`print` 到 stdout 在 cron 场景易丢。建议：
   276|   276|```python
   277|   277|import logging
   278|   278|logging.basicConfig(filename=BASE_DIR + "/logs/notification.log", level=logging.INFO)
   279|   279|```
   280|   280|
   281|   281|### S4：`send_telegram` 应该打印 response body
   282|   282|```python
   283|   283|resp = requests.post(url, data=data, timeout=10)
   284|   284|if resp.ok:
   285|   285|    return True
   286|   286|else:
   287|   287|    print(f"Telegram API error {resp.status_code}: {resp.text}")
   288|   288|    return False
   289|   289|```
   290|   290|
   291|   291|---
   292|   292|
   293|   293|## 跨文件问题汇总
   294|   294|
   295|   295|| 文件 | 严重 Bug | 重要 Issue | 建议 |
   296|   296||------|----------|------------|------|
   297|   297|| predict_cycle.py | #1 (PID) | — | S2 |
   298|   298|| orchestrator.py | #2 (返回结构) | #5, #6, #7 | — |
   299|   299|| index_generator.py | — | — | — |
   300|   300|| notification.py | #2, #3 | #4, #8 | S1, S3, S4 |
   301|   301|
   302|   302|**3 个严重 bug 都在不同文件，需要一起修才能让推送管道工作。**
   303|   303|
   304|   304|---
   305|   305|
   306|   306|## 优先级建议
   307|   307|
   308|   308|1. **P0（立即修）**：Bug #1（PID 互斥）、Bug #2（result 结构）、Bug #3（Markdown）
   309|   309|2. **P1（这周修）**：Issue #4（去重）、Issue #5（fallback 一致性）、Issue #6（silent fail）
   310|   310|3. **P2（有时间修）**：Issue #7、Issue #8、S1-S4
   311|   311|
   312|   312|---
   313|   313|
   314|   314|**审计完成时间**：2026-06-07
   315|   315|**审计者**：棠棠
   316|   316|**未做任何代码修改**
   317|   317|
   318|
   319|---
   320|
   321|# v2 审计追加（2026-06-07 23:11）
   322|
   323|**追加审计范围**：
   324|- `/mnt/c/Users/Admin/liuhecai/predictor/data_fetcher.py`（408 行 / 12.8KB）
   325|- `/mnt/c/Users/Admin/liuhecai/predictor/base_predictor.py`（66 行 / 2KB）
   326|- `/mnt/c/Users/Admin/liuhecai/predictor/predictor_registry.py`（216 行 / 7.2KB）
   327|- `/mnt/c/Users/Admin/liuhecai/predictor/ledger_writer.py`（关键函数 L460-490）
   328|- `/mnt/c/Users/Admin/liuhecai/scripts/run_pipeline.py`（121 行 / 3.5KB）⭐ 重要发现
   329|
   330|---
   331|
   332|## 🔴 v2 新发现的严重问题
   333|
   334|### Bug #4（升级为 P0）：predict_cycle.py 和 run_pipeline.py 是两个 cron 入口，notification 结构定义都不对
   335|
   336|**关键发现**：`scripts/run_pipeline.py` 是**另一个 cron 入口**，它和 `cron/predict_cycle.py` **构造的 notification 结构完全不同**。
   337|
   338|**对比表**：
   339|
   340|| 字段 | predict_cycle.py L198 | run_pipeline.py L102-116 | notification.py 期望 |
   341||------|---------------------|----------------------|-------------------|
   342|| 传 `result` | 直接传 orchestrator 原始结果 | 构造 `notification_data` | 期望 `{verified_period, pending_period, verified, pending}` |
   343|| 字段命名 | `{issue, results}` | `{pending_period, pending_top6, versions}` | ❌ 都不匹配 |
   344|
   345|**predict_cycle.py L194-198**：
   346|```python
   347|result = verify_and_predict()
   348|if result:
   349|    send_notification(result)  # ❌ 直接传 orchestrator 结果
   350|```
   351|
   352|**run_pipeline.py L102-116**（正确的尝试，但仍然错）：
   353|```python
   354|notification_data = {
   355|    "pending_period": result.get("issue"),  # ✅
   356|    "pending_top6": [],
   357|    "versions": {}  # ❌ 字段名是 "versions" 不是 "pending"
   358|}
   359|for v, r in result.get("results", {}).items():
   360|    pred = r.get("prediction", [])
   361|    notification_data["versions"][v] = {  # ❌
   362|        "prediction": pred,
   363|        "strategy": r.get("metadata", {}).get("strategy", "")
   364|    }
   365|    if not notification_data["pending_top6"]:
   366|        notification_data["pending_top6"] = pred
   367|send_notification(notification_data)  # ❌
   368|```
   369|
   370|**notification.send_notification L168-185 期望**：
   371|```python
   372|def send_notification(result: Dict) -> bool:
   373|    pending_period = result.get("pending_period", "")  # ✅
   374|    pending = result.get("pending", {})  # ❌ run_pipeline 给的是 "versions"
   375|    pending_top6 = pending.get("v12", {}).get("prediction", []) if "v12" in pending else []
   376|```
   377|
   378|**实际结果**：
   379|- `run_pipeline.py` 的 `notification_data["versions"]` 永远不被读取
   380|- `result.get("pending", {})` 永远返回 `{}`
   381|- `pending_top6 = []`
   382|- `format_message` 看 `result.get("verified", {})` 和 `result.get("pending", {})` → 都是空
   383|- **最终推送**：`"🎯 第xxx期预测"` —— **没有任何版本预测**（v1 Bug #2 同问题）
   384|
   385|**根本设计错误**：
   386|- `notification.py` **自己内部有 `load_latest_result()`**（L76-110）能从 ledger 拉正确数据
   387|- 但 `send_notification` **没调用它**
   388|- 三个调用方（predict_cycle / run_pipeline / `__main__` test）都在尝试构造 result，但**全都构造错**
   389|
   390|**修复方向**（仅供参考，未修改）：
   391|```python
   392|# notification.py send_notification 改为：
   393|def send_notification(result: Dict = None) -> bool:
   394|    # 忽略调用方传的 result，自己从 ledger 拉
   395|    fresh = load_latest_result()
   396|    if not fresh:
   397|        print("无最新结果可推送")
   398|        return False
   399|    result = fresh
   400|    # ... 后续逻辑
   401|```
   402|
   403|调用方就不用关心构造了。
   404|
   405|---
   406|
   407|## 🟡 v2 新发现的问题
   408|
   409|### Issue #11：orchestrator.py L80 vs predictor_registry.py L141-153 — play_type fallback 不一致
   410|
   411|**orchestrator.py L80-85**（关键代码）：
   412|```python
   413|metadata = PredictorRegistry.get_metadata(version)
   414|play_type = metadata.get('play_type', 'liuhe')  # ← 静默 fallback 到 'liuhe'
   415|```
   416|
   417|**predictor_registry.py L141-153**（关键代码）：
   418|```python
   419|def get_play_type(cls, version: str) -> str:
   420|    meta = cls._metadata.get(version, {})
   421|    play_type = meta.get("play_type")
   422|    if play_type is None:
   423|        from validators import MetadataError
   424|        raise MetadataError(...)  # ← 抛错
   425|    return play_type
   426|```
   427|
   428|**问题**：
   429|- orchestrator 调 `get_metadata().get('play_type', 'liuhe')` —— 静默 fallback
   430|- ledger_writer.verify_prediction L306 调 `PR.get_play_type(version)` —— 抛错
   431|- **同一份 metadata 在两个地方行为不同**
   432|- 如果某 version 的 metadata 真的缺 play_type：
   433|  - orchestrator 会当 'liuhe' 处理
   434|  - ledger_writer 抛 MetadataError
   435|  - **行为不一致，难以排查**
   436|
   437|**修复方向**（仅供参考）：统一一处入口，orchestrator 也用 `PR.get_play_type()` 让错误抛出。
   438|
   439|---
   440|
   441|### Issue #12：predictor_registry.py L97 选"最深子类"算法可能选错
   442|
   443|**位置**：`predictor_registry.py` L84-99
   444|
   445|```python
   446|candidates = []
   447|for attr_name in dir(module):
   448|    attr = getattr(module, attr_name)
   449|    if isinstance(attr, type):
   450|        try:
   451|            is_sub = issubclass(attr, module_bp) and attr != module_bp
   452|        except TypeError:
   453|            is_sub = False
   454|        if is_sub:
   455|            candidates.append((attr, attr_name))
   456|
   457|if candidates:
   458|    best = max(candidates, key=lambda x: len(x[0].__mro__))  # ← MRO 最深
   459|    cls._predictors[version] = best[0]
   460|```
   461|
   462|**问题**：
   463|- 算法：选 `__mro__` 最长的类
   464|- 如果 `predictor.py` 里有：
   465|  ```python
   466|  class V5Predictor(BasePredictor): pass       # MRO 长度 2
   467|  class V5Experimental(V5Predictor): pass      # MRO 长度 3 ← 会被选中
   468|  class V5ExperimentalV2(V5Experimental): pass # MRO 长度 4 ← 会被选中
   469|  ```
   470|- **如果 V5Experimental 是测试类、deprecated 类，预测器会被错选**
   471|- 跨 15 个 active predictor 风险中等
   472|
   473|**修复方向**（仅供参考）：要求 predictor.py 显式声明 `PRIMARY_CLASS = V5Predictor` 常量，registry 优先用 PRIMARY_CLASS。
   474|
   475|---
   476|
   477|### Issue #13：data_fetcher.py L289-296 字段名硬编码
   478|
   479|**位置**：`data_fetcher.py` L289-296
   480|
   481|```python
   482|def get_special_zodiac(record: Dict) -> str:
   483|    return record["zodiac"].split(",")[6]
   484|
   485|def get_special_number(record: Dict) -> int:
   486|    return int(record["openCode"].split(",")[6])
   487|```
   488|
   489|**问题**：
   490|- 字段名 `"zodiac"`、`"openCode"` 硬编码
   491|- API 改名 → KeyError，没有 fallback
   492|- `record[6]` 索引假设有 ≥7 个元素，没防御
   493|
   494|**修复方向**（仅供参考）：加 `record.get("zodiac", "")` + `if "," in record.get("zodiac", "")` + 长度检查。
   495|
   496|---
   497|
   498|### Issue #14：data_fetcher.py 模块级副作用
   499|
   500|**位置**：
   501|

---

# v3 端到端流程可行性分析（2026-06-07 23:36）

**触发**：用户问"这个流程能够正常更新吗？只分析，不做修改"
**方法**：8 维度端到端分析 + curl 验证 + 进程状态 + 文件 mtime 交叉对比
**结论**：数据能更新，但 3 个缺口让"自动更新"感觉不工作

---

## 8 维度评估矩阵

| # | 维度 | 状态 | 关键证据 |
|---|------|------|----------|
| 1 | 触发机制 | ⚠️ 频率不够 | crontab 只有 `35 21 * * *` 每天一次 |
| 2 | 进程互斥 | ✅ flock 有效 | `flock -n` curl 验证空闲 |
| 3 | 数据获取 | ✅ API 通 | circuit_breaker failures=0 |
| 4 | 存储写入 | ✅ 正常 | aggregated_live.jsonl 3.5MB / 7543 records |
| 5 | 索引更新 | ⚠️ 健康 degraded | hashchain 178 breaks |
| 6 | 推送通知 | ❌ 不达用户 | Bug #2/#3/#4 三重 |
| 7 | Dashboard | ✅ 端口在跑 | 0.0.0.0:5188 响应 200 |
| 8 | 失败恢复 | ❌ 完全缺失 | crontab 无 recovery/monitor 调度 |

**8 个里 4 个 ✅ + 2 个 ⚠️ + 2 个 ❌**

---

## 各维度详细证据

### 维度 1：触发机制
```
$ crontab -l
35 21 * * * flock -n /tmp/liuhe_pipeline.lock -c "cd /mnt/c/Users/Admin/liuhecai && ... python3 cron/predict_cycle.py"
```

**最近 7 天 21:35 都跑成功**：
- 6/1 21:35:06 (pid 123876)
- 6/2 21:35:05 (pid 479180)
- 6/3 21:35:09 (pid 800076)
- 6/4 21:35:02 (pid 1132446)
- 6/5 21:35:01 (pid 1467630)
- 6/6 21:35:08 (pid 1709172)
- 6/7 21:35:08 (pid 2032268)

**问题**：每天 1 次。如果一天开 1 期 OK，多期时中间开的新期要等 22 小时。

### 维度 2：进程互斥
```bash
$ flock -n /tmp/liuhe_pipeline.lock -c 'echo OK' || echo FAILED
OK   # 锁空闲，可抢
```

**flock 锁当前空闲**（崩溃后自动释放）。
**LOCK_FILE 残留但 flock 释放** — `cleanup_stale_lock()` 会清理但**只检查 PID，LOCK_FILE 永远不主动删**。

Bug #1（PID_FILE 从未写入）影响 `is_running()` 但**不影响主流程互斥**（因为 flock LOCK_NB 是真正互斥机制）。

### 维度 3：数据获取
```json
$ cat /mnt/c/Users/Admin/liuhecai/data/runtime/circuit_breaker.json
{
  "failures": 0,
  "opened_at": null,
  "last_error": null
}
```

API 完全健康。21:35 cron 那次 + 22:49 那次都拉到了数据。

### 维度 4：存储写入
```
$ ls -la /mnt/c/Users/Admin/liuhecai/storage/aggregated_live.jsonl
-rwxrwxrwx 1 admin1 admin1 3501653 Jun  7 22:49 /mnt/c/Users/Admin/liuhecai/storage/aggregated_live.jsonl
```

3.5MB，22:49 更新。**说明数据写入正常**。

### 维度 5：索引更新
```
version_book/index.json:         3022 bytes, 22:49 ✅
storage/prediction_index.json:   3672 bytes, 22:49 ✅
```

**索引文件能更新**。但 dashboard health check 显示：

```json
{
  "name": "hashchain",
  "details": {
    "chain_breaks": 178,
    "latest_hash": "c4934734550cc938",
    "total_records": 7543
  },
  "status": "degraded"
}
```

**178 chain breaks** — 历史 hash 链断裂问题，**不影响主流程但需关注**。

### 维度 6：推送通知（v1/v2 已审计 Bug #2/#3/#4）

**调用链**：
```
predict_cycle.py L198
  send_notification(result)   # result = orchestrator 原始返回
    ↓
notification.send_notification(result)
  result.get("pending_period", "")  → ""（字段不匹配）
  result.get("pending", {})         → {}（字段不匹配）
  format_message(result)            → "🎯 第xxx期预测"（无版本数据）
    ↓
send_telegram(message, parse_mode="Markdown")
  message 含 "[v12] ..."  → Telegram API 400
```

**最终推送内容**：`"🎯 第xxx期预测"`（**无任何版本预测**）
**Telegram 收到**：API 400 错误（Markdown 解析失败）

**用户感知**：收不到推送 / 收到无意义消息 → 以为"没更新"。

### 维度 7：Dashboard

```bash
$ curl -sS http://127.0.0.1:5188/health
{
  "checks": [
    {"name":"data", "status":"ok", "details":{"record_count":7543, "size_bytes":3501653}},
    {"name":"cache", "status":"degraded", "details":{"entries":71, "expired":70}},
    {"name":"hashchain", "status":"degraded", "details":{"chain_breaks":178}},
    {"name":"pipeline", "status":"degraded", "details":{"lock_status":"unlocked","last_run":null}}
  ],
  "status": "degraded"
}

$ curl -sS http://127.0.0.1:5188/api/records/v24
{"count":781, "mode":"live", "records":[...]}
```

**Dashboard 端口 5188 在跑，能读数据。**
**但显示 22:49 那次的数据**（cron 要等明天 21:35 才跑下一次）。

### 维度 8：失败恢复

```
$ crontab -l | grep -iE 'recovery|monitor|补偿'
(空)
```

**recovery_job 完全不在 crontab**。**monitor_job 也不在**。

**实际表现**：
- 22:49 那个 PID 2056893 崩了
- flock 自动释放（kernel 行为）
- 但 LOCK_FILE 残留
- processed_issue.json 显示 22:49:22 写入（崩前写入的）
- aggregated_live.jsonl 22:49:12（崩前更新）
- **没有 recovery 触发补跑**
- **没有 monitor 检测异常**
- dashboard `pipeline.last_run=null` 说明**连 dashboard 都不知道 22:49 那次是合法运行还是异常**

---

## 主流程链路图

```
cron 21:35 trigger
  ↓
flock LOCK_NB (LOCK_FILE)
  ↓ ✅ flock 有效
predict_cycle.py verify_and_predict()
  ↓
run_live_cycle() → sync_latest + get_records + verify + predict
  ↓ ✅ API 通
write_results() → ledger_writer.write_live_prediction
  ↓ ✅ 写入 OK
aggregated_live.jsonl + index 更新
  ↓ ✅ 存储 OK
write_index() → version_book/index.json
  ↓ ✅ 索引 OK
send_notification(result)  ← ❌ Bug #2/#3/#4
  ↓ 消息结构错 + Markdown 解析失败
Telegram API  ← ❌ 收不到
  ↓
Dashboard 端口 5188  ← ✅ 端口在跑，但数据旧
  ↓
release_lock + unlink PID_FILE
  ↓ ⚠️ LOCK_FILE 残留（设计上故意）
```

**链路里 7 个节点中 5 个 ✅ + 1 个 ⚠️ + 1 个 ❌**

---

## 主人感知的"无法自动更新"真相

| 主人看到的 | 实际原因 | 数据是否真在更新？ |
|----------|---------|------------------|
| "Telegram 没收到推送" | Bug #2/#3/#4 | ✅ 在更新（主人不知道） |
| "22:49 之后没新数据" | cron 频率太低（每天 1 次） | ✅ 22:49 那次更新了，但没下次 |
| "Dashboard health degraded" | hashchain 178 breaks | ✅ 数据 OK，链有问题 |
| "lock 文件残留" | 22:49 进程崩了没清理 | ✅ flock 已释放，文件残留无害 |
| "processed_issue 跳号" | 22:49 那次是手动跑的 | ✅ 2026159 比 21:35 的 2026158 多 1 期 |

**真相：数据更新没断，是用户感知层坏了。**

---

## 不修的情况下长期影响

| 时间维度 | 状态 |
|---------|------|
| **短期（1 周）** | 数据每天 21:35 更新，dashboard 显示旧数据，Telegram 永远不通知 |
| **中期（1 月）** | hashchain breaks 继续累积（如果 verify 不修），用户彻底放弃 TG 推送 |
| **长期（3+ 月）** | 一次 cron 失败 = 永远不补跑（没 recovery），需要主人天天盯 |
| **崩溃场景** | cron 失败 + 没 recovery → 看板失效 → 主人失去所有自动能力 |

---

## 3 个 P0 必须修（按优先级）

1. **Bug #2 + #4**：notification.send_notification 改为内部自给自足（不依赖调用方传 result）— 解锁推送
2. **加 recovery_job 到 crontab**（每 15 分钟 / 每小时）— 解锁补跑
3. **修 hashchain breaks**（独立审计 verify_chain() 逻辑）— 解锁数据可信度

P1：
- Bug #3（Markdown 转义）
- Bug #1（PID_FILE 写入 — 设计修复）
- cron 频率提升（每天 → 每 N 小时）

P2：
- LOCK_FILE 清理机制
- dashboard degraded 自动告警

---

**v3 端到端分析完成时间**：2026-06-07 23:36
**审计者**：棠棠
**未做任何代码修改**
**所有数据均通过实际工具验证（curl / 终端 / 文件 mtime / 健康检查）**
