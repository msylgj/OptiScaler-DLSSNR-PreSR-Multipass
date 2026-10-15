---
project: OptiScaler-DLSSNR-PreSR-Multipass
content_language: zh
content_language_source: default
model_context_window: 1000000
model_context_window_source: default
current_sprint: 1
status: planning
baseline_commit: 1bd39091337cc07ba961c8e59ded57e21dc95b18
---

# OptiScaler 简体中文翻译项目简报

## 1. 项目定位

- 为现有 Windows C++ 游戏 mod 提供简体中文文档及设置界面，不创建新产品，不移植 Aurora 功能。
- 唯一工作根：`D:/Documents/GitHub/OptiScaler-DLSSNR-PreSR-Multipass`。
- 用户 fork：<https://github.com/msylgj/OptiScaler-DLSSNR-PreSR-Multipass>；基线及 origin 已由用户提供，本次核对 HEAD 匹配。

## 2. 用户与问题

- 面向使用 NVIDIA RTX 和受支持游戏的中文用户，消除安装说明、配置解释和设置文案的语言障碍。
- 不替用户改变性能、画质、游戏兼容性、安全建议或运行库选择。

## 3. 成功标准

- 40 份基线一方 Markdown 全部有中文对应，原有中文段落保留；正文、警告、表格、历史说明不因篇幅而省略。
- 设置标签、选项、帮助、通知、悬浮提示及 NR 面板全部登记并翻译；技术名称和保护项有逐项保留理由。
- 配置有效行、算法、默认参数、调用顺序、ID、日志、版权许可、依赖和构建配置保持保护契约。
- required local / Windows build / manual gates 有同一 artifact 的实际证据；未运行不是通过。

## 4. 默认范围

- 文档：基线全部 40 份一方 Markdown，含根目录、`docs/`、NR 源码目录中的设计/开发/forwarder 文档和 bug 模板的中文副本。
- 文档入口：保留英文 `README.md` 原字节，新增 `README.zh-CN.md` 作为中文入口；其他对应文档位于 `docs/zh-CN/<原始相对路径>`。
- INI：只翻译全行注释；所有有效行及技术示例保持。
- UI：公共菜单、NR 面板，以及菜单外已有通知；动态状态生产者必须完成追踪，不将未知来源当作已覆盖。
- 安装器：本次完整调查全部显示文案；默认只规划中文对照说明。是否改写实际安装脚本尚无明确授权。

## 5. 非目标与保护项

- 不更改渲染、超分、帧生成、NR、输入、默认值、功能开关、运行库、依赖、下载 URL、版本或发布行为。
- 不翻改 LICENSE、Licenses、第三方源码/文档、版权声明、作者名、API、配置键、枚举、数值、文件名、格式参数、隐藏 ID、日志模板及其技术数据。
- 不增设国际化框架、语言切换、字体下载、遥测或系统工具；Aurora 只作术语/方法参考。
- 本次不编辑任何已有源码/文档、配置或脚本，不测试应用，不提交、推送、建分支、发布 Issue/PR、调用子代理。

## 6. 已有技术与证据

| 项目 | 已核实事实 | 限制 |
| --- | --- | --- |
| UI 入口 | DX / overlay 调用 `MenuCommon::Init/RenderMenu`，主菜单调用 `DlssNr::RenderMenu` | 不能只翻 menu 目录 |
| ID | vendored `ImHashStr` 中 `##` 不重置哈希，`###` 连井号一起参与后续哈希 | 简单保留后缀不能证明旧 ID 不变 |
| 字体 | HQ 加载 Hack/用户 TTF，非 HQ 无中文回退；ImGui 为 1.92.0 WIP | 未实测 cmap/atlas，不保证中文可见 |
| 编码 | vcxproj 为 Unicode，已读选项无 `/utf-8` | 项目 Unicode 属性不证明窄字节 UTF-8 |
| 构建 | VS2022 v143、Windows SDK 10.0；已有 x64 solution 配置 | 编译器不在 PATH，10 个子模块未初始化 |
| 验证复用 | `tests/` 现有专项 C++ smoke；无翻译不变性工具 | 计划一个 PowerShell 验证脚本，不新增应用依赖 |

- 可重放源码锚点与外部只读参考见 [范围证据](docs/sprint-1/scope-evidence.md)。

## 7. 当前阶段

- Producer 调查与规划已落盘，Sprint 保持 `planning`，实现完成数 `0/5`。
- 本轮不从 Producer 自动进入 Dev/QA；用户已限定只规划、禁止子代理。
- 主动识别的范围冲突：纯字符串替换不能保证字体、原 ID 和 label 驱动帮助分派不受影响。

## 8. 交接与决策

- Dev 输入：[计划](docs/sprint-1/plan.md)、[完整清单](docs/sprint-1/inventory.md)、[运行上下文](docs/sprint-1/runtime-context.md)、[进度](docs/sprint-1/progress.md)。
- A1 的清单/验证工具和 B1/B2 的新增中文文档不依赖 UI 授权；本次仍不启动。
- D1 必须先结算字体/ID/共享日志边界。C1 的实际安装脚本改写必须先确认范围和终端编码可行性。
- 更新第 7、8 节是实际阶段过渡的前提；未过门禁不得写完成或正式 QA 签署。

## 9. 信息组织与术语

- 统一术语建议：超分辨率、帧生成、多帧生成、神经渲染、预设、运动矢量、反应遮罩；保留 DLSS、DLSSD、DLAA、XeSS、FSR、NR、HDR、API 等技术标识。
- 以目标原文为含义依据；Aurora 提供术语候选，不把它的能力、兼容结论或参数带入译文。
- 中文首页清楚区分目标项目与 Aurora；不将原下载/反馈链接擅自改到尚无发行产物的 fork。

## 10. 实施路径

- 5 个任务：A1 清单/最小验证器，B1 根文档，B2 其余完整文档，C1 INI/安装文案对照，D1 完整 UI。
- 串行 DAG、每节点范围与机械关联、派生预算、全部门禁在 Dev 前定义于计划。
- 共享术语和 coverage manifest，禁止 worktree/并行写共享文件；派生提交预算不代表提交授权。

## 11. 验证策略

- 本机可用 PowerShell 7 + Git：未来执行词法白名单、INI 有效行、格式参数、ASCII 技术串、完整 ID、覆盖率、链接/代码块、编码检查。
- 编译和字形/游戏交互分别验证，静态不变性不代替编译，编译不代替 GPU 游戏 UI。
- QA 手动验收路径见 [验收规程](docs/qa/acceptance-1.md)；这不是 signoff。

## 12. 风险与开放问题

- O1：是否授权最小中文字体支持、显示文案/内部身份分离及必要共享日志边界支持？未授权；不改变渲染算法或默认参数。
- O2：实际安装器汉化是否纳入交付？若纳入，是否允许必要的代码页支持？未授权；不执行真实安装脚本作试验。
- O3：谁提供 VS2022/子模块齐备的构建环境和可用 GPU/游戏验收环境？当前无可用证据。
- O4：NR 动态状态函数的完整定义/返回文案尚未定位，A1 必须解决；若基线缺定义，作为原有构建疑点单列，不在翻译中顺手修复。
- O5：当前禁止 commit，HEAD 不能唯一绑定未来脏工作树产物；正式 L2/QA 的 revision 协议需先结算，不能伪写 SHA 通过。

## 13. 授权与质量管理

- 只新增本轮规划文档；没有应用改动、远程副作用或系统工具安装授权。
- 使用受路径约束的编辑工具；源码/翻译实现由后续 Dev 执行，QA 测试由后续 QA 执行。
- 缺少 CodeGraphy 工具按一次降级记账；无 canonical backlog 和前序 Sprint，不创建空经验规则，不虚构 trial pass。
- 规划配置的 `1000000` 是默认上下文窗口值，不是本机测量或当前 token 使用量。

## 14. 资料与交付状态

- [脑暴](docs/brainstorm/translation-decisions.md)、[漂移基线](docs/sprint-1/drift-check.md)、[计划](docs/sprint-1/plan.md)、[进度](docs/sprint-1/progress.md)、[上下文](docs/sprint-1/runtime-context.md)、[范围证据](docs/sprint-1/scope-evidence.md)、[完整清单](docs/sprint-1/inventory.md)、[验收规程](docs/qa/acceptance-1.md)。
- 未创建 done、L4 结果或 QA signoff；没有权威 L2 PASS。本次交付仅为完整规划及可执行性说明。