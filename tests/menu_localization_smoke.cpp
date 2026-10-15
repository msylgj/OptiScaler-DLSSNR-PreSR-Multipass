#include "../OptiScaler/include/imgui/imgui.h"
#include "../OptiScaler/include/imgui/imgui_internal.h"
#include "../OptiScaler/menu/localization/Localization.h"
#include "../OptiScaler/menu/localization/Mount.h"

#include <cassert>
#include <cfloat>
#include <cstring>
#include <iostream>

int main(int argc, char** argv)
{
    assert(argc == 3);
    assert(MenuLocalization::Load(argv[1]));
    assert(MenuLocalization::Translate("Save Settings") == "\xe4\xbf\x9d\xe5\xad\x98\xe8\xae\xbe\xe7\xbd\xae");
    assert(MenuLocalization::Translate("unmapped upstream text").empty());
    assert(MenuLocalization::Translate("OptiScaler - Press Insert to open menu").find("Insert") != std::string::npos);
    assert(MenuLocalization::Translate("Press D:\\Games\\{1}\\game.exe for more info").find("D:\\Games\\{1}\\game.exe") != std::string::npos);

    // Replay complete strings from v0.8.91 producers, not isolated printf arguments.
    const std::pair<const char*, const char*> branchCases[] = {
        { "Auto (reuse Blackwell kernel)", "自动（复用 Blackwell 内核）" },
        { "Applied: rewrite blend weight, 2 descriptor(s)", "已应用：重写混合权重，2 个描述符" },
        { "Applied: reuse Blackwell kernel, 3 kernel group(s)", "已应用：复用 Blackwell 内核，3 组内核" },
        { "Not applied: PTX is 2048 bytes, expected 4096.", "未应用：PTX 为 2048 字节，预期为 4096。" },
        { "Not applied: found 2 midpoint multiplies, expected 4.", "未应用：找到 2 处中点乘法，预期为 4。" },
        { "Not applied: no compatible Blackwell interpolation kernel image.", "未应用：没有兼容的 Blackwell 插值内核映像。" },
        { "Streamline plugin ceiling: patched.", "Streamline 插件帧数上限：已修补。" },
        { "AUTO", "自动" },
        { "ON", "开启" },
        { "ON 4x", "开启 4x" },
        { "Rendered frame: 10.00 ms", "渲染帧：10.00 ms" },
        { "Rendered frame: 10.00 ms (NR overlaps/exceeds this interval)",
          "渲染帧：10.00 ms（NR 与此间隔重叠或超出此间隔）" },
        { "Current method: Game's XeLL (RTSS) (inactive)", "当前方式：游戏的 XeLL (RTSS)（未生效）" },
        { "Running.  (model running, edit hidden)", "正在运行。（模型运行中，改动已隐藏）" },
        { "Running natively on Vulkan - 12.5 ms elapsed  (model running, edit hidden)",
          "正在 Vulkan 上原生运行 - 耗时 12.5 ms（模型运行中，改动已隐藏）" },
        { "Private upscale: waiting for NR evaluation; clean SR frame retained",
          "独立放大：正在等待 NR 计算；保留未修改的 SR 帧" },
        { "Private upscale: running: 1280x720 contribution -> private DLSS -> 1920x1080; applied after SR",
          "独立放大：运行中：1280x720 改动 → 独立的 DLSS → 1920x1080；在 SR 之后应用" },
        { "Private upscale: private DLSS creation failed: CreateFeature returned 0xBAD00001; clean SR frame retained",
          "独立放大：独立的 DLSS 创建失败：CreateFeature 返回 0xBAD00001；保留未修改的 SR 帧" },
        { "Private upscale: private DLSS creation failed: NGX initialization or required entry point unavailable; clean SR frame retained",
          "独立放大：独立的 DLSS 创建失败：NGX 初始化或所需入口点不可用；保留未修改的 SR 帧" },
        { "Private DLSS SR: EvaluateFeature returned 0xBAD00002", "独立 DLSS SR：EvaluateFeature 返回 0xBAD00002" },
        { "Fallback to ordinary NR: NGX rejected the packed model input", "回退至普通 NR：NGX 拒绝了打包模型输入" },
        { "Unavailable: invalid frame or global scale", "不可用：帧或全局缩放比例无效" },
        // Vulkan displays the same reason without the DX12 prefix.
        { "invalid frame or global scale", "帧或全局缩放比例无效" },
        { "Spatial compression 1920x1080 → 1280x720 (44.4% pixels)", "空间压缩 1920x1080 → 1280x720（44.4% 像素）" },
        { "Output Scaling is DISABLED, Target Res: 1920x1080 (1.50)\nJitter Count: 8",
          "输出缩放已禁用，目标分辨率：1920x1080（1.50）\n抖动次数：8" },
        { "Designed primarily for downscaling.\nRetains good contrast with minimal artefacts, but softer than Lanczos.\n\nOnly FSR1 and Bicubic are supported when Ratio is below 1.0.",
          "主要为缩小设计。\n能保持较好对比度，瑕疵很少，但比 Lanczos 更柔和。\n\n比例低于 1.0 时，仅支持 FSR1 和双三次。" },
        { "You are missing the following dlls from the streamline folder:\n- sl.dlss.dll\n- sl.dlss_g.dll\n",
          "streamline 文件夹缺少以下 DLL：\n- sl.dlss.dll\n- sl.dlss_g.dll\n" },
    };
    for (const auto& [source, expected] : branchCases)
    {
        const auto actual = MenuLocalization::Translate(source);
        if (actual != expected)
            std::cerr << "Translation mismatch: " << source << "\nActual: " << actual << "\nExpected: " << expected << '\n';
        assert(actual == expected);
    }
    // Removed main-only features must not survive through an obsolete catch-all.
    assert(MenuLocalization::Translate("Residual DLSS: not started (NR frames 2, skipped 1)").empty());
    assert(MenuLocalization::Translate("Pre-SR changes: not started (NR frames 2, skipped 1)").empty());
    assert(MenuLocalization::messages.count("Kernel Image") == 0);

    ImGui::CreateContext();
    auto& io = ImGui::GetIO();
    io.IniFilename = nullptr;
    io.DisplaySize = ImVec2(1280, 720);
    io.DeltaTime = 1.0f / 60.0f;
    io.BackendFlags |= ImGuiBackendFlags_RendererHasTextures;
    io.Fonts->AddFontDefault();
    ImFontConfig chineseConfig;
    chineseConfig.MergeMode = true;
    assert(io.Fonts->AddFontFromFileTTF(argv[2], 13.0f, &chineseConfig));
    ImGui::NewFrame();
    ImGui::SetNextWindowSize(ImVec2(600, 400));
    ImGui::Begin("Localization test");
    const auto originalId = ImGui::GetID("Save Settings##original");
    MenuLocalization::enabled = false;
    assert(ImGui::GetID("Save Settings##original") == originalId);
    MenuLocalization::enabled = true;
    const char label[] = "Intensity";
    ImGui::Button(label);
    assert(ImGui::GetCurrentContext()->LastItemData.ID == ImGui::GetID(label));
    assert(std::strcmp(label, "Intensity") == 0);
    const auto translated = MenuLocalization::Translate("Save Settings");
    assert(ImGui::CalcTextSize("Save Settings##original", nullptr, true).x == ImGui::CalcTextSize(translated.c_str()).x);
    const char* remaining = nullptr;
    ImGui::GetFont()->CalcTextSizeA(ImGui::GetFontSize(), FLT_MAX, 0, label, nullptr, &remaining);
    assert(remaining == label + std::strlen(label));
    for (float scale : { 0.5f, 1.0f, 2.0f })
    {
        ImGui::PushFontSize(13.0f * scale);
        auto* baked = ImGui::GetFont()->GetFontBaked(ImGui::GetFontSize());
        const auto checkGlyphs = [&](const std::string& text)
        {
            const char* position = text.c_str();
            const char* end = position + text.size();
            while (position < end)
            {
                unsigned int codepoint = 0;
                const int count = ImTextCharFromUtf8(&codepoint, position, end);
                assert(count > 0);
                if (codepoint >= 0x4e00 && codepoint <= 0x9fff)
                    assert(baked->FindGlyphNoFallback(static_cast<ImWchar>(codepoint)));
                position += count;
            }
        };
        for (const auto& message : MenuLocalization::messages)
            checkGlyphs(message.second);
        for (const auto& pattern : MenuLocalization::patterns)
            checkGlyphs(pattern.translation);
        ImGui::RenderTextEllipsis(ImGui::GetWindowDrawList(), ImVec2(20, 40), ImVec2(55, 60), 55,
                                 "Save Settings", nullptr, nullptr);
        ImGui::TextWrapped("Loading may pause the game and look like a freeze. Please wait.");
        ImGui::PopFontSize();
    }
    ImGui::TextWrapped("Save Settings");
    ImGui::LogToBuffer();
    ImGui::SeparatorText("Upscalers");
    const auto captured = std::string(ImGui::GetCurrentContext()->LogBuffer.c_str());
    assert(captured.find("Upscalers") != std::string::npos);
    ImGui::LogFinish();
    const auto drawEditor = [&](const char* id, bool localized, bool active, bool elide = false)
    {
        MenuLocalization::enabled = localized;
        ImGui::SetCursorPos(ImVec2(20, 300));
        ImGui::SetNextItemWidth(elide ? 35 : 220);
        if (active)
        {
            ImGui::GetCurrentContext()->NavActivateId = ImGui::GetID(id);
            ImGui::GetCurrentContext()->NavActivateFlags = ImGuiActivateFlags_PreferInput;
        }
        char value[32] = "Intensity";
        const int before = ImGui::GetWindowDrawList()->VtxBuffer.Size;
        ImGui::InputText(id, value, sizeof(value), elide ? ImGuiInputTextFlags_ElideLeft : ImGuiInputTextFlags_None);
        assert(!active || ImGui::IsItemActive());
        assert(std::strcmp(value, "Intensity") == 0);
        return ImGui::GetWindowDrawList()->VtxBuffer.Size - before;
    };
    const int originalInactive = drawEditor("##originalInactive", false, false);
    assert(drawEditor("##localizedInactive", true, false) == originalInactive);
    const int originalActive = drawEditor("##originalActive", false, true);
    assert(drawEditor("##localizedActive", true, true) == originalActive);
    const int originalElided = drawEditor("##originalElided", false, true, true);
    assert(drawEditor("##localizedElided", true, true, true) == originalElided);
    ImGui::End();
    ImGui::Render();
    assert(ImGui::GetDrawData()->TotalVtxCount > 0);
    ImGui::DestroyContext();
    assert(!MenuLocalization::Load(std::filesystem::path(argv[1]) / "missing.json"));
    assert(MenuLocalization::Translate("Save Settings").empty());
    std::cout << "PASS: dictionary, captures, real ImGui layout/clipping, Chinese glyphs at 3 scales, original labels/IDs, input editing, capture logs, fallback\n";
}