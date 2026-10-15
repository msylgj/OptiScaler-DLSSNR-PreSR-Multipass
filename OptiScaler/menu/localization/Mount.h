#pragma once

#include "Localization.h"
#include "../../include/imgui/imgui.h"

#ifdef _WIN32
#include <Windows.h>
#endif

namespace MenuLocalization
{
inline void Mount(const std::filesystem::path& dllDirectory, ImGuiIO& io, float size)
{
    if (!Load(dllDirectory / "OptiScaler" / "locales" / "zh-CN.json"))
        return;
    enabled = false;
#ifdef _WIN32
    wchar_t windowsDirectory[MAX_PATH] {};
    const auto length = GetWindowsDirectoryW(windowsDirectory, MAX_PATH);
    if (length == 0 || length >= MAX_PATH)
        return;
    const auto directory = std::filesystem::path(windowsDirectory) / "Fonts";
    for (const auto* filename : { "msyh.ttc", "Deng.ttf", "simhei.ttf", "simsun.ttc" })
    {
        const auto path = directory / filename;
        std::error_code error;
        if (!std::filesystem::is_regular_file(path, error) || error)
            continue;
        if (io.Fonts->Fonts.empty())
            io.Fonts->AddFontDefault();
        ImFontConfig config;
        config.MergeMode = true;
        config.PixelSnapH = true;
        config.Flags |= ImFontFlags_NoLoadError;
        const auto utf8 = path.u8string();
        if (io.Fonts->AddFontFromFileTTF(reinterpret_cast<const char*>(utf8.c_str()), size, &config))
        {
            enabled = true;
            return;
        }
    }
#else
    (void) io;
    (void) size;
#endif
}
}