---
sprint: 1
status: planning
content_language: zh
baseline_commit: 1bd39091337cc07ba961c8e59ded57e21dc95b18
force_sequential: true
commit_authorized: false
branch_creation_authorized: false
source_implementation_authorized_this_turn: false
---

# Sprint 1 翻译计划

## 范围与边界

- 目标：完整简体中文文档及设置界面；功能、默认参数、配置键/有效值、渲染和依赖不变。40 份原文逐份对应，清单见 [inventory.md](inventory.md)。
- 本轮只做 Producer 规划，不启动 A1-D1，不写测试脚本或应用实现，不运行 QA/构建。
- 中文策略：英文 README 原字节不动，未来新增 README.zh-CN.md；其余 39 份镜像到 docs/zh-CN/<基线相对路径>。代码块、版权、第三方、技术标识原样保留。
- 安装脚本的可见文案完整调查，但实际脚本汉化是范围待确认项；默认 C1 提供中文对照文档和 INI 注释。若用户要求实际安装器全部中文而不允许必要编码支持，完整安装器交付可能阻塞，不能称已完成。
- O1：字体、控件身份及共享日志边界支持没有授权。D1 保留完整范围并阻塞，不缩成仅 tooltip 翻译；任何必要非字符串改动须先由用户裁决、更新 plan/具体槽位清单，不能依靠 mechanical_links 自动放权。
- O2：本机没有编译器/GPU 游戏证据；真实构建与手工门禁保留 required。
- O3：禁 commit/branch 下，未来脏工作树不能只用 HEAD 冻结；先绑定规范化工作树内容摘要作观察证据，但不把它伪装为正式 L2/QA SHA。后续正式 revision 协议需单独批准。

## 本 Sprint 不做什么

- 不移植 Aurora 的代码、功能、库、默认值、字体搜索/转换框架、安装/下载逻辑或游戏兼容方案。
- 不改构建配置、依赖、运行库、算法、输入处理、参数、许可证、日志或技术字符串；不顺手修复基线缺陷。
- 不创建分支/worktree，不 commit/push/PR/Issue，不触发 workflow、下载安装器/字体/系统工具，不读凭据/jsonl。
- 不以“有中文字符”“diff 仅字符串”“CI workflow 存在”替代覆盖率、语义不变性、构建或游戏验证。

## 任务与可行性前置 Gate

| 节点 | 内容与消费者 / G1 | G2 heat | 完成条件 |
| --- | --- | --- | --- |
| A1 | 术语表、源单元 manifest、一个验证器；入口为本计划 gate CLI，消费者 Dev/L2/QA | cold, low-ROI；正确性工具非性能优化 | 基线清单完整；未知槽位 fail closed；所有负向样例被拒；不更改基线文件 |
| B1 | 根文档 8 份中文版本；消费者从 README.zh-CN.md 访问所有使用/配置/历史说明 | cold, low-ROI；完整翻译是用户目标 | 8/8 文件、逐段覆盖和代码块/链接对照成立 |
| B2 | 其余一方文档 32 份，含历史 review、源码设计文档和 bug 模板中文副本 | cold, low-ROI；不因低频删范围 | 40/40 总覆盖，已有中文保留，镜像导航闭合 |
| C1 | INI 全行注释、7 个安装/下载/构建脚本文案中文对照；实际脚本写入待确认 | cold, low-ROI；直接面向安装/配置用户 | 配置有效行严格相同；所有显示槽位有译文/保留理由；未授权脚本原字节相同 |
| D1 | 真实后端 -> MenuCommon -> NR 面板；菜单外 toast 与动态状态消费者一并覆盖 | hot（显示）, warm（交互）；不是 perf 任务 | O1 结算、完整翻译、ID/状态/日志保持、真实 Windows/GPU gates 通过 |

- G1：已见生产调用者为 menu_dx_base、menu_overlay_base、主菜单 NR 调用；不是仅 test/bench 入口。
- D1 的 FinishedPictureStatus 目前只定位到声明/显示消费者，A1 必须解析实际定义与字符串数据流；未解析视为覆盖缺口，不假定整个 dlssnr 模块可写。
- G3/G4：不适用，不是性能 Sprint；不运行 bench、profile，不提出性能收益。

## Task DAG

```yaml
drift_whitelist: []
task_dag:
  nodes:
    - id: A1
      desc: "完整翻译目录、术语和最小不变性验证器"
      depends_on: []
      coupling: none
      estimated_tokens: high
      force_sequential: true
      target_rules:
        globs:
          - "tests/check_translation.ps1"
          - "docs/sprint-1/translation-map.json"
          - "docs/zh-CN/GLOSSARY.md"
          - "docs/sprint-1/progress.md"
          - "docs/sprint-1/runtime-context.md"
        modules: []
        languages: [powershell, json, markdown]
        mechanical_links:
          - type: callers
            of: [tests/check_translation.ps1]
    - id: B1
      desc: "根目录全部八份文档中文镜像"
      depends_on: [A1]
      coupling: strong
      estimated_tokens: high
      force_sequential: true
      target_rules:
        globs:
          - "README.zh-CN.md"
          - "docs/zh-CN/CONTRIBUTING.md"
          - "docs/zh-CN/Changelog.md"
          - "docs/zh-CN/Config.md"
          - "docs/zh-CN/Features.md"
          - "docs/zh-CN/INSTALL-DLSSNR.md"
          - "docs/zh-CN/Issues.md"
          - "docs/zh-CN/Spoofing.md"
          - "docs/zh-CN/GLOSSARY.md"
          - "docs/sprint-1/translation-map.json"
          - "docs/sprint-1/progress.md"
        modules: []
        languages: [markdown, json]
        mechanical_links:
          - type: callers
            of: [README.md, INSTALL-DLSSNR.md, Config.md]
    - id: B2
      desc: "全部剩余三十二份文档镜像及导航"
      depends_on: [B1]
      coupling: weak
      estimated_tokens: high
      force_sequential: true
      target_rules:
        globs:
          - "docs/zh-CN/docs/**"
          - "docs/zh-CN/OptiScaler/dlssnr/**"
          - "docs/zh-CN/.github/ISSUE_TEMPLATE/crash-bug.md"
          - "docs/zh-CN/GLOSSARY.md"
          - "docs/sprint-1/translation-map.json"
          - "docs/sprint-1/progress.md"
        modules: []
        languages: [markdown, json]
        mechanical_links:
          - type: callers
            of: [docs/CREDITS.md, OptiScaler/dlssnr/README.md]
    - id: C1
      desc: "INI 注释和安装器文案中文对照，实际脚本改写待确认"
      depends_on: [B2]
      coupling: weak
      estimated_tokens: medium
      force_sequential: true
      target_rules:
        globs:
          - "OptiScaler.ini"
          - "docs/zh-CN/installer-messages.md"
          - "docs/zh-CN/GLOSSARY.md"
          - "docs/sprint-1/translation-map.json"
          - "docs/sprint-1/progress.md"
        modules: []
        languages: [ini, markdown, json]
        mechanical_links:
          - type: callers
            of: [OptiScaler.ini, setup_windows.bat, setup_linux.sh]
    - id: D1
      desc: "完整公共菜单、NR 面板、既有通知及动态状态；边界授权前阻塞"
      depends_on: [C1]
      coupling: strong
      estimated_tokens: high
      force_sequential: true
      target_rules:
        globs:
          - "OptiScaler/menu/menu_common.cpp"
          - "OptiScaler/dlssnr/DlssNr_Menu.cpp"
          - "OptiScaler/dllmain.cpp"
          - "OptiScaler/hooks/Reflex_Hooks.cpp"
          - "docs/zh-CN/GLOSSARY.md"
          - "docs/sprint-1/translation-map.json"
          - "docs/sprint-1/progress.md"
        modules: []
        languages: [cpp, markdown, json]
        mechanical_links:
          - type: callers
            of: [OptiScaler/menu/menu_common.cpp, OptiScaler/dlssnr/DlssNr_Menu.cpp]
          - type: callees
            of: [OptiScaler/dlssnr/DlssNr_Menu.cpp]
  properties:
    max_antichain_width: 1
    critical_path_depth: 5
    coupling_density: 0.5
    coupling_density_basis: "four direct edges: (0.7 + 0.3 + 0.3 + 0.7) / 4"
    layers: [[A1], [B1], [B2], [C1], [D1]]
    recommended_topology: sequential
task_sizing:
  task_count: 5
  strong_coupling_count: 2
  dag_layers: 5
  dag_width: 1
  historical_bug_per_sprint: 1
  historical_bug_source: cold-start-default-no-history
  base: 5
  coupling_bonus: 2
  bug_reserve: 1
  derived_commit_budget: 8
  warn_threshold: 16
  hard_cap: 10
  authorized_commits: 0
  authorized_branch_creations: 0
```

- 推导：`8 = 5 + 2 + 1`，未超过 hard cap；`16 = 5*3+1` 是拆分预警而非可用提交数，不能覆盖 hard cap。
- 强耦合节点为 B1、D1；其余弱耦合仍因共享术语/manifest/进度串行，依赖链不表示可并行资源许可。
- mechanical_links 用于只读影响分析，不绕过确切文件、字符串槽位及禁止修改项。无 CodeGraphy 时使用 PowerShell Select-String / git grep，保留降级记录。

## 最小验证器规格

- A1 只新增一个 `tests/check_translation.ps1`，复用 PowerShell/.NET/Git；目前 tests 为专项 smoke 风格，没有可复用翻译工具。不得安装依赖或用 grep 正则冒充完整 C++ 解析器。
- 输入：`-Baseline` 固定 SHA、`-Map` JSON 单元清单、`-Check` 选择器；以脚本路径推导根并校验与唯一根一致。支持未提交新增译文，不依赖 `git diff --name-only` 排除未跟踪文件。
- 清单字段至少：schema_version、baseline、source_path、source_blob、unit_id、lexical/context anchor、source_text、target_path、target_text、kind、status、preserve_reason、protected_spans、format_contract、id_contract、consumers、authorization。保持一对一 occurrence，不以全局字符串替换归并重复文案。
- 译文状态为 translated / already-zh / preserve / blocked；自然语言分母包含 blocked，未授权不能变成 preserve。保护项只按具体技术片段，不允许整文件无理由排除。

| 检查 | 可执行契约与失败条件 |
| --- | --- |
| invariants / scope | 用 Git 基线 blob 对比真实工作树字节及未跟踪新增文件；只允许节点路径和已批准槽位。外部库、许可证、构建、默认参数、二进制、日志、源注释全部冻结。不是 diff 行白名单 |
| invariants / C++ | 有状态词法扫描区分注释、char、普通/宽/u8/相邻拼接/raw 字符串、预处理续行；仅精确 manifest 范围的显示字面量可变化。其余 token 序列（类型、字面量前缀、数值、运算、调用/参数顺序）严格相同；无法识别则拒绝，不把所有字符串抹成一个占位后比较 |
| invariants / INI | 只允许首个非空字符为分号的全行注释改变；其余行逐字节、有序比较，重复节/重复键不得被字典吞掉。值中的分号、空白、大小写、默认 auto、数值、示例技术参数不变 |
| invariants / formats | 解码字符串后比较 printf 有序说明符（宽度/精度/长度、位置、星号参数、%%、%n）、std::format/fmt 字段与 spec、转义、内嵌 NUL/换行；数量、顺序、类型/格式必须一致，不新增裸 % |
| invariants / IDs | 区分 ## 与 ###、纯隐藏字符串、表格/child/window ID、PushID 栈、动态索引、ScopedCollapsingHeader、DeferredSlider/Reset 拼接和 strcmp。静态等价先比较目标哈希规范；动态无法静证必须列 blocked 并真实探针。不得将 中文###旧标签 当作原 ID 等价证明 |
| invariants / ASCII | 原样保留每单元技术白名单及非显示所有字符串：API/枚举/资源状态、键、路径、DLL、URL、版本、数值、单位/倍率、热键、日志及动态日志参数来源；未知字符串保守拒绝 |
| invariants / scripts | 默认所有 7 个脚本整文件冻结。若后续授权，先更新 plan 和清单；PS 用原生 AST 限定 Write-Host/提示参数，BAT/SH 用精确提示槽位并逐字节保持其余语法，未知结构 fail closed；echo 生成卸载脚本的可执行 payload 不能整行豁免 |
| coverage | 从基线独立枚举 40 份 Markdown 和 UI/INI/安装显示单元，与 manifest 双向核对；检测遗漏、重复、越界和新增未登记英文自然语言。文件覆盖 40/40，单元覆盖 100%，blocked=0 才能完整通过；不能以出现中文或删分母过门禁 |
| docs | 一对一 source/target 映射；保留原文件。fenced/indented code、inline code、HTML 技术区、frontmatter 机器字段按保护跨度对照；中文副本 bug 模板的人类 name/about 可翻但字段名冻结，且不激活为实际模板。外部 URL 原样；本地路径唯一允许按镜像 map 重定位，片段必须存在，原标题锚点用显式 alias 保留。不修原文陈旧链接，基线断链精确单列，禁止新增断链 |
| encoding | 严格 UTF-8 解码、禁止 U+FFFD/非预期 BOM、保持原换行；新 Markdown UTF-8。C++ 首选可验证的 ASCII UTF-8 字节转义候选，检查 hex 转义贪婪和相邻字面量，不直接把 u8 char8_t 传给 const char*。不依赖 Unicode 工程属性或系统 ACP。真实执行字节另由 Windows gate 验证 |
| selftest | 内存中合法翻译应接受；INI 值/重复键顺序、非显示字符串、数字/运算符、printf/format、##/###/父栈、strcmp 不同步、技术串、代码块/链接、无效 UTF-8、未跟踪越界文件各至少一个反例应拒绝。必须逐例返回拒绝原因；在生产文件上制造变异或自动回滚均禁止 |

- 先做负向 selftest 再开放翻译；首个便宜反证是 `Intensity` 调用/比较不同步和 `Change Upscaler##2` 哈希变化。验证器不能因边界困难降低检查。
- JSON 是结构化数据，用 ConvertFrom-Json/ConvertTo-Json；进度/计划契约复用宿主 `kixpower-contract.ps1`，不为本项目复制一套 YAML 正则。

## Verifiable Gates

- 以下为唯一 gate manifest；`type` 取 local_gate / ci_gate / manual_gate，全部 `required: true`，Dev 前已定义。命令工作目录必须为项目根；命令中的相对路径是此运行契约，不是当前已存在的脚本承诺。
- 本机 PowerShell/Git 可执行静态方法，但脚本尚未由 Dev 实现；因此所有未来应用门禁均为 NOT_RUN。

```yaml
verifiable_gates:
  - id: TR-SELFTEST
    type: local_gate
    cmd: "pwsh -NoProfile -File tests/check_translation.ps1 -Baseline 1bd39091337cc07ba961c8e59ded57e21dc95b18 -Map docs/sprint-1/translation-map.json -Check selftest"
    expect: "exit=0; legal fixtures accepted; every negative fixture rejected with reason"
    required: true
  - id: TR-INVARIANTS
    type: local_gate
    cmd: "pwsh -NoProfile -File tests/check_translation.ps1 -Baseline 1bd39091337cc07ba961c8e59ded57e21dc95b18 -Map docs/sprint-1/translation-map.json -Check invariants"
    expect: "exit=0; exact scope, INI effective lines, C++ non-display tokens, formats, IDs, ASCII and script invariants preserved; unresolved=0"
    required: true
  - id: TR-COVERAGE
    type: local_gate
    cmd: "pwsh -NoProfile -File tests/check_translation.ps1 -Baseline 1bd39091337cc07ba961c8e59ded57e21dc95b18 -Map docs/sprint-1/translation-map.json -Check coverage"
    expect: "exit=0; documents=40/40; natural-language units=100 percent; blocked=0; no missing, duplicate or unregistered unit"
    required: true
  - id: TR-DOCS
    type: local_gate
    cmd: "pwsh -NoProfile -File tests/check_translation.ps1 -Baseline 1bd39091337cc07ba961c8e59ded57e21dc95b18 -Map docs/sprint-1/translation-map.json -Check docs"
    expect: "exit=0; code/protected spans preserved; original files unchanged; links resolve or match exact baseline debt; URL retargets=0"
    required: true
  - id: TR-ENCODING
    type: local_gate
    cmd: "pwsh -NoProfile -File tests/check_translation.ps1 -Baseline 1bd39091337cc07ba961c8e59ded57e21dc95b18 -Map docs/sprint-1/translation-map.json -Check encoding"
    expect: "exit=0; strict encoding and newline policy; all runtime string bytes specified; no compiler/codepage assumption"
    required: true
  - id: TR-WIN-RELEASE
    type: ci_gate
    cmd: "msbuild OptiScaler.sln /m /t:Rebuild /p:Configuration=Release /p:Platform=x64 /verbosity:minimal"
    expect: "exit=0; actual Windows x64 Release DLLs and build logs bound to source snapshot"
    required: true
  - id: TR-FORMAT
    type: ci_gate
    cmd: "clang-format --dry-run --Werror OptiScaler/menu/menu_common.cpp OptiScaler/dlssnr/DlssNr_Menu.cpp OptiScaler/dllmain.cpp OptiScaler/hooks/Reflex_Hooks.cpp"
    expect: "clang-format major=20; exit=0; no unrelated reformat; any authorized added C++ file extends manifest before implementation"
    required: true
  - id: TR-GLYPHS
    type: manual_gate
    cmd: "MANUAL M-GLYPHS: execute docs/qa/acceptance-1.md against the built target-version atlas and DLL"
    expect: "actual translated codepoints and runtime UTF-8 bytes verified; HQ, non-HQ and custom font paths have evidence; no replacement glyphs"
    required: true
  - id: TR-GAME-UI
    type: manual_gate
    cmd: "MANUAL M-UI: execute docs/qa/acceptance-1.md in supported Windows GPU game paths"
    expect: "all UI families inspected; identical ID/state/config behavior; no text overlap; DX11, native DX12, Vulkan and relevant overlay paths evidenced or explicitly blocked"
    required: true
  - id: TR-INSTALL-ENCODING
    type: manual_gate
    cmd: "MANUAL M-INSTALL: execute docs/qa/acceptance-1.md for localized installer text or byte-identical exclusion evidence"
    expect: "default untranslated scripts byte-identical and Chinese transcript complete; if authorized, isolated display/input corpus works on CP936 and CP437/65001 without executing installer actions"
    required: true
  - id: TR-SEMANTICS
    type: manual_gate
    cmd: "MANUAL M-TEXT: execute docs/qa/acceptance-1.md source-target review"
    expect: "complete natural-language coverage, terminology and warnings faithful; no Aurora capabilities, altered defaults or unsupported claims"
    required: true
```

| Gate 组 | 可执行性 / 负责人 | 当前证据 |
| --- | --- | --- |
| 5 个 local_gate | Dev 实现后本机可运行；权威结果由后续 Orchestrator 记录 | NOT_RUN；本次只校验规划 schema，不算 local gates |
| TR-WIN-RELEASE | Windows 构建机/获准的只构建环境，需 v143、SDK、10 个已锁定子模块及既有依赖；不是本机现成能力 | NOT_RUN；不得触发带发布副作用的既有 workflows |
| TR-FORMAT | clang-format 20 主机，沿用已读 CI 的版本/排除原则 | NOT_RUN；本机工具缺失 |
| 4 个 manual_gate | QA/具备 GPU、游戏和字体环境的操作者；MANUAL 是规程调用，不是可直接运行的 shell 命令 | NOT_RUN；规程和证据字段已给出，不伪造截图、数值或通过 |

## 冻结、交接与停止条件

- 验证以 `baseline SHA + tracked/untracked path/blob/byte hash + built DLL SHA256 + gate manifest SHA256` 留证；这仅补足脏工作树观察，不自行替换团队正式 SHA 信任链。
- 禁止为了满足 freeze 自作主张 commit/branch。未解决 O3 时，正式 L2/QA 占位保持空；主线程不得写权威 L2 PASS。
- 后续正式 L2：复用宿主 `Get-KixRequiredLocalGates`、`Get-KixGateManifestJson`、`Get-KixSha256` 排序规范化 5 个 required local gates；代码/测试/清单/gate 变化后全量失效，记录 stash refs 不操作 stash。
- CI 未跑可记录 pending，手工未完成不能包装为 CONDITIONAL；完整 UI/字体阻塞不属于“仅 CI pending”。
- 每个任务按触及风险跑 focused gate；最终所有 required gates 对同一冻结产物成立才可收尾。实现阶段由 Dev 自测、Orchestrator 权威 L2、QA 实际验证；本次不替他们执行。
- 无前序 Sprint、无 backlog，eval 为 not triggered，不编造 L4 学习或 trial pass；详见漂移基线。