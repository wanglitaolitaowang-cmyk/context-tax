# Context Tax

**定位重复上下文，分清实测与猜测。**

面向 Codex 优先的本地只读“上下文体检”Skill，附 Python 审计脚本。检查一个明确选定的会话日志，列出已记录的输入/缓存/输出用量、重复工具文本和可复核的行号，再提出最小流程改进。

这不是无人涉足的赛道。TokenScope 已有 Claude Code 的 CLI + Skill；context-audit、ccusage、context-mode 等也覆盖相关需求。本项目只提供一个独立实现、范围收窄、对未知字段保守处理的版本，不宣称首创、比竞品成熟或已证明省钱。参见 [来源与现有方案](skills/context-tax/references/sources.md)。

## 它实际会做什么

脚本把日志中的累计用量正确拆分和去重，区分新输入、缓存读取、缓存写入与输出；找到不同工具调用返回的完全相同文本、过长工具结果和重复记录的指令段落。每个发现带原始 JSONL 行号，不把“重复”直接等同于“浪费”。

Skill 根据报告解释可能原因，最多提出三条有证据的动作，例如：先定位再读小范围、对未变化的资料复用已有证据、完整输出留在本地而非反复塞进会话。修改流程需经用户同意；不自动修改 AGENTS.md、CLAUDE.md、config.toml、MCP、权限、PATH、历史或源代码。

**CLI 完全离线，Python 3.10+，只用标准库，不需要账号、API Key、pip 或 npm。** 调用它的 Codex/Claude 模型本身仍按其正常方式联网/计量；不是整个工作流免费或离线。Skill 的限制是行为指令，不是宿主工具权限沙箱。

## Windows 安装

先解压完整 ZIP，进入包含 install.py 的 `context-tax-skill` 文件夹，再在 PowerShell 中运行：

```powershell
py -3 --version
py -3 install.py --target codex --dry-run
py -3 install.py --target codex
py -3 install.py --target codex --check
```

已有 Python 3.10+ 但没有 `py` 启动器时，把 `py -3` 替换成 `python`。未安装 Python 时，本包不会自行下载或安装。

当前 Codex 默认安装到 `$HOME\.agents\skills\context-tax`；Claude 使用 `--target claude`，安装到 `$HOME\.claude\skills\context-tax`。安装脚本只创建新 Skill 目录，不接管现有配置。同名目录已存在时拒绝覆盖；`--check` 只核对包内文件，不验证额外本地文件。异常中断可能留下新建的半成品目录，需要先检查，不会自动清理。

在 Codex 的 Skill 选择入口选择 Context Tax，或显式提及 `$context-tax`；不同宿主界面可能不同。未显示时重启宿主再检查。Claude Code 使用 `/context-tax`。两端均配置为显式调用，不在每轮自动运行。安装字节核对不等于真实宿主已经加载成功。

自定义安装位置：`python install.py --dest "D:\example\context-tax"`，末级目录必须是 context-tax。该命令不会使任意目录自动成为宿主搜索路径。升级/卸载由用户查看并处理这一独立 Skill 目录，本包不提供全盘清理或强制覆盖命令。

## 先用样例验证，不安装也能运行

```powershell
py -3 skills/context-tax/scripts/context_tax.py audit --source codex --log tests/fixtures/codex-synthetic.jsonl
py -3 -m unittest discover -s tests -v
```

样例是构造数据，不是真实客户会话。查看 [样例说明](examples/README.md) 和 [样例报告](examples/codex-sample-report.md)。

## 给 Codex 的使用提示词

```text
使用 $context-tax 做一次只读上下文体检。
先用 metadata-only discover 列出最多 5 个候选日志；不要自动把最新日志当成当前项目。
如果不能确定目标，给我候选让我选。确认后只审计一个日志，不读取全部历史。
不要把完整日志灌进会话，不改配置，不删文件，不上传。
分开列出日志记录值、字节级观察/粗估值和未知项。
最多给三条有行号证据的改进建议，解释必要复查等可能原因。
未经我同意不应用优化，不承诺省钱百分比。
```

已经有日志路径时直接指定，不必再发现：

```powershell
py -3 skills/context-tax/scripts/context_tax.py audit --source codex --log "D:\your-logs\selected-session.jsonl"
```

`D:\your-logs\selected-session.jsonl` 是占位路径，必须替换。最好选择已经完成、不会继续写入的会话。一个会话可能包含多个任务，不能自动算成单个任务成本。

导出报告时选择不存在的新文件名，例如 `--json-out report-01.json --md-out report-01.md`。默认上限：单文件 64 MiB、每行 4 MiB、200,000 行。范围不足会报告限制，不自动扫描更多文件。终端报告为精简英文；Skill 应用中文解释，JSON 键名保持稳定。

## 能测与不能测

| 项目 | 本版口径 |
|---|---|
| fresh/cached/write/output | 已支持字段中的日志记录值；缺失不补零 |
| 缓存比例与命中请求率 | 分别计算并给出有效记录覆盖，不能混为一谈 |
| 重复工具返回与指令 | 完全相同的文本/段落、UTF-8 字节及行号，不是已证实的无效成本 |
| Tool schema | 仅显式提供的清单/支持的请求快照；字节数与标注的 bytes/4 粗估 |
| 精确 token replay ratio | 未知；常规会话日志不等于完整请求抓包 |
| 成本 | OpenRouter 已报告 credits；或调用者给出模型价格后的 API 等价估算 |
| 单成功任务成本 | 还需声明单任务、PASS 和验收文件，且计量完整；不代替真实验收 |
| 压缩省钱、可避免成本 | 未知；没有因果验证，不自动编造百分比 |

### 可选价格、schema 和比较

`--prices` 接受调用者核对过的模型价格 JSON，每百万 Token 美元单价。只按精确模型名称匹配，没有当前价格自动下载。examples/prices.example.json 的价格与模型均为虚构，不可当真。正数桶缺价、模型未知或多请求聚合区间不能定价。

`--schemas` 接受 `{"tools":[...]}` 或工具数组，不启动或查询 MCP。安装清单大不等于每轮全部发送。更不要把高缓存占比视为 85% 浪费，或将 bytes/4 宣称成精确 Token 数。

比较两次已导出报告：

```powershell
py -3 skills/context-tax/scripts/context_tax.py compare before.json after.json
```

只有满足同一 `--case`、双方 `--outcome pass`、各自 `--acceptance` 验收文件、完整计量和相同已知模型等最低条件，才输出观察到的下降比例。case 必须代表可比的任务、代码/数据/环境和验收条件。验收文件只是哈希存证，脚本不会证明 PASS 真实成立。即使通过门槛，单组前后对比也不是压缩效果的因果证明。

## 兼容性与已验证范围

Codex 是主要设计目标；Claude Code、OpenRouter 是附带的已知 JSONL 结构适配器。不是“所有版本通吃”。OpenRouter 只接受提供的逐行最终响应/请求响应对，不支持任意后台 CSV、SSE 或实时抓包。子代理文件不自动汇总。具体字段和限制见 [适配器说明](skills/context-tax/references/adapters.md)。

**此次交付：Linux / Python 3.13.5 下 71 项自动测试通过；三类构造样例 CLI 运行通过。尚未执行用户 Windows、本机真实日志或 Codex Desktop 的端到端验收，也未证明任何实际节省。** 测试不会把“全绿”包装成“实操一定没问题”。详见 TESTING.md。

退出码：0 = 支持字段的 OBSERVED 计量，不等于无问题；2 = 有效但不完整的 PARTIAL 报告；1 = 输入/格式/文件错误。

## 隐私与安全边界

报告不包含原始提示词、命令参数、绝对路径或任意自定义工具名；用行号和稳定别名引用。别名/哈希不是完全匿名，统计与模式仍可能敏感，公开前应复核。discover 会显示本机路径，只供本地选文件。模型读取原文范围须遵守用户授权与宿主隐私设置。

本项目不是权限沙箱、脱敏认证、账单审计认证或防误删工具。脚本对输入只读，仅在明确要求时新建输出文件；安装程序另行创建 Skill 目录。不要把不可信日志的内容作为指令执行。

MIT License。可自行建立 GitHub 仓库公开；本次未自动发布、未安装到用户机器、未连接账户。
