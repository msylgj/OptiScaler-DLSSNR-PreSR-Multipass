# 界面译文维护

`zh-CN.json` 仅用于游戏内菜单、帮助、通知及载入提示，不修改配置、日志或渲染功能。

## 使用

- 编译后的 DLL 从自身所在目录读取 `OptiScaler/locales/zh-CN.json`，与游戏的工作目录无关。
- Release 构建与打包脚本会复制词典；手动部署时保留这个相对目录。
- 修改 JSON 后重启游戏即可生效，不必重新编译 DLL。
- 移除词典、词典无效或系统没有受支持的中文字体时，界面回退英文。
- 中文字形使用 Windows 已安装的微软雅黑、等线、黑体或宋体，不下载或分发字体。

## 更新

- `messages` 的键是原始英文显示文本，值是中文。键区分大小写；换行写作 `\n`。
- 不带 ImGui 的 `##` / `###` 隐藏标识。业务标签和 ID 始终保留原文。
- `patterns` 匹配已经格式化的完整文本，用 `{0}`、`{1}` 顺序捕获动态值。
- 译文保留同一组捕获标记；不要把 `%s`、`%d` 等格式参数写进规则。
- 固定文本精确匹配优先，动态规则按文件顺序匹配。具体规则放在通用规则之前。
- 未命中的上游新文案显示英文；不要翻译技术标识、文件名、URL 或错误码。

源码挂接仅在 `menu_common.cpp` 的初始化和 ImGui 的字形测量、绘制、省略号及输入框显示边界。
更新 ImGui 时保留这些 `MenuLocalization` 挂接，不需要逐个修改控件或 NR 面板。

## 验证

在仓库根目录使用 WSL 中的 GCC，测试使用实际中文字体和 ImGui 内置 stb 字体后端：

```sh
g++ -std=c++20 -Wall -Wextra -include tests/menu_localization_config.h -IOptiScaler/include/imgui tests/menu_localization_smoke.cpp OptiScaler/include/imgui/imgui.cpp OptiScaler/include/imgui/imgui_draw.cpp OptiScaler/include/imgui/imgui_widgets.cpp OptiScaler/include/imgui/imgui_tables.cpp -o /tmp/optiscaler-menu-localization
/tmp/optiscaler-menu-localization OptiScaler/locales/zh-CN.json /mnt/c/Windows/Fonts/msyh.ttc
```

此测试不替代 Windows DLL 构建和游戏内 DX11 / DX12 / Vulkan 的实际验收。
