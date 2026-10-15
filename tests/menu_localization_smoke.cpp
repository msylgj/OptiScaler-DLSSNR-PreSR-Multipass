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