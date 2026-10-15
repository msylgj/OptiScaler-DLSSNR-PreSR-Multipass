# Sprint 1 范围证据

- 基线：`1bd39091337cc07ba961c8e59ded57e21dc95b18`；唯一根目录：`D:/Documents/GitHub/OptiScaler-DLSSNR-PreSR-Multipass`。
- 状态：规划调查，不是实现、L2 或 QA 通过记录。本次只新增规划资料。

## 控制路径

| 证据 | 机制事实 | 规划影响 |
| --- | --- | --- |
| `OptiScaler/menu/menu_dx_base.cpp:18,51`、`menu_overlay_base.cpp:30,38` | 实际后端调用公共 Init / RenderMenu | 菜单是生产可达路径，不是仅测试代码 |
| `OptiScaler/menu/menu_common.cpp:7164` | 主菜单调用 `DlssNr::RenderMenu` | 完整设置汉化必须包括 `OptiScaler/dlssnr/DlssNr_Menu.cpp`，不能只翻 menu 目录 |
| `OptiScaler/menu/menu_common.cpp:7950` 附近 | HQ 分支只加载用户字体或内置 Hack；非 HQ 没有中文回退路径 | 不得宣称只换字符串就能默认显示中文 |
| `OptiScaler/menu/menu_common.cpp:2468` | 按钮标签为 `Change Upscaler##2` | 保留 `##2` 不等于保留整个控件身份 |
| `OptiScaler/include/imgui/imgui.cpp:2349-2355` | 哈希契约明确只有 `###` 重置此前哈希 | 文案变动必须比较完整 ID 输入/栈，而非仅对照后缀 |
| `OptiScaler/dlssnr/DlssNr_Menu.cpp:52` | 滑块辅助函数使用 `ImGui::GetID(label)` | ID 变化可能影响控件编辑状态，须检查辅助函数消费者 |
| `OptiScaler/OptiScaler.vcxproj:41,136,199` | `CharacterSet=Unicode`、`stdcpplatest`，已读配置无 `/utf-8` | Unicode 项目属性不能替代窄字符串 UTF-8 字节验证；构建配置禁止修改 |

## 深一层的反例

| 证据 | 可观察风险 | 最小验证 |
| --- | --- | --- |
| `OptiScaler/dlssnr/DlssNr_Menu.cpp:48-103` | `pending` 按 label 哈希保存，`Reset##` 拼接 label；`strcmp(label, "Intensity")` 等决定提示文本 | 必须逐对检查调用 label、比较常量、重置 ID 和 pending 的共同身份；只改一处会失去对应 HelpMarker |
| `OptiScaler/include/imgui/imgui.cpp:2349-2391` | `###` 后的哈希包含三个井号本身 | `中文###旧标签` 不保证等于原来的无井号 ID，禁止把这种写法当作已经证明的 ID 保持方案 |
| `OptiScaler/menu/menu_common.cpp:3329,3342,3726` | 选项标签也进入日志参数 | 冻结日志模板还不够；翻译共享 label 会改变日志内容，须标记数据流边界，不能默默放行 |
| `OptiScaler/include/imgui/imgui.h:31-32` | vendored ImGui 标记为 `1.92.0 WIP` / `19196` | 不能套用其他稳定版 glyph-range 结论；动态字形及后端纹理支持必须针对目标版本验证 |
| `setup_windows.bat:17-32,86-104` | 安装器提示与删除/跳转/用户输入交织 | 禁止直接执行安装器取证；静态白名单必须区分当前 echo、输入提示和生成卸载脚本的 echo |

- ID 数值变化是机制事实，不自动等于已证明的持久化回归；本项目 `io.IniFilename = nullptr`。但完整 ID 原样保留是本次保护契约，任何例外必须明确授权，不能靠“看起来能点”替代。
- `strcmp` 的自然语言常量可以作为一组字符串同步翻译候选；这不能自动解决哈希身份、日志共享和字体问题。是否采用显示/内部标识分离属于待授权的最小边界支持，当前不决策实现。
- 中文字形是否实际缺失仍需字体 cmap / atlas 检查，不把“没有回退”单独当作所有用户字体都不能显示中文的证明。

## 可反证假设

| ID | 局部假设 | 首个低成本反证检查 | 当前结论 |
| --- | --- | --- | --- |
| H1 | 只换显示字符串且不改字体即可默认汉化 | 检查 Init 两分支；在字体 cmap 中查 `设置` 等实际译文字形，检查对应嵌入字体来源 | 默认字体支持尚未实测；现有路径没有中文回退，不能接受 H1 为确定依据 |
| H2 | 保留 `##` 后缀即可保持 ID | 按目标 ImHashStr 算法比较 `Change Upscaler##2` 与中文同后缀标签 | 源码契约已反驳该简化规则；精确数值检查待 Dev/QA |
| H3 | 保存 UTF-8 文件即可让 MSVC 窄字面量输出 UTF-8 | 对已选字符表示做 MSVC 字节级探针，不改变工程选项 | 未验证；可评估 ASCII `\u` / UTF-8 字节转义，不引入转换框架 |

## Aurora 参考隔离

- 参考 revision：`bde8bcdc56fa8cc5ec7763acc24bdcbc1aaa4041`，只读来源：<https://github.com/abc354402600/OptiScaler-Aurora>。
- 已读固定 revision 的 `OptiScaler/menu/menu_common.cpp`：使用 `AURORA_CN` / `AuroraUtf8` 转换，另有 `FindChineseFallbackFont` / `AddChineseFontFallback`，对用户字体、HQ/非 HQ 分支作了适配。
- 来源：<https://raw.githubusercontent.com/abc354402600/OptiScaler-Aurora/bde8bcdc56fa8cc5ec7763acc24bdcbc1aaa4041/OptiScaler/menu/menu_common.cpp>。
- 只参考“超分辨率、帧生成、预设、运动矢量”等术语及原文保留方式；不复制宏、字体搜索、默认值、运行库同步、渲染或游戏兼容逻辑。
- Aurora 成功显示中文的实现不是目标项目具备相同能力的证据。

## 范围判断

- 文档翻译可独立推进；完整默认中文 UI 不能在“所有非字符串 token、字体初始化和 ID 输入一律不变”的约束下预先承诺可行。
- 必须保留完整 UI/安装器验收面，不能删除困难项后称完整汉化。必要的字体/ID/终端编码支持仅作为待授权边界；本次不实施。
- 已有用户自定义 TTF 选项不等于默认中文可用，不得通过改 INI 默认字体路径规避约束。
- 若用户坚持零边界支持改动且没有等价可行路径，则完整 UI 交付保持阻塞；不自动降为仅文档翻译。