#pragma once

#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

#include "../../../external/nlohmann/json.hpp"

namespace MenuLocalization
{
struct Pattern
{
    std::vector<std::string> parts;
    std::string translation;
};

inline std::unordered_map<std::string, std::string> messages;
inline std::vector<Pattern> patterns;
inline bool enabled = false;
inline thread_local bool suppressed = false;

class UntranslatedText
{
        bool previous;

    public:
        explicit UntranslatedText(bool suppress) : previous(suppressed) { suppressed |= suppress; }
        ~UntranslatedText() { suppressed = previous; }
        UntranslatedText(const UntranslatedText&) = delete;
        UntranslatedText& operator=(const UntranslatedText&) = delete;
};

inline bool Load(const std::filesystem::path& path)
{
    enabled = false;
    messages.clear();
    patterns.clear();
    try
    {
        std::error_code error;
        if (std::filesystem::file_size(path, error) > 1024 * 1024 || error)
            return false;
        std::ifstream stream(path, std::ios::binary);
        const auto document = nlohmann::json::parse(stream);
        messages = document.at("messages").get<decltype(messages)>();
        for (const auto& entry : document.at("patterns"))
        {
            Pattern pattern;
            const auto source = entry.at("source").get<std::string>();
            pattern.translation = entry.at("target").get<std::string>();
            size_t start = 0;
            for (size_t index = 0;; ++index)
            {
                const auto marker = "{" + std::to_string(index) + "}";
                const auto position = source.find(marker, start);
                if (position == std::string::npos)
                {
                    pattern.parts.push_back(source.substr(start));
                    break;
                }
                pattern.parts.push_back(source.substr(start, position - start));
                start = position + marker.size();
            }
            bool hasLiteral = false;
            for (size_t index = 0; index < pattern.parts.size(); ++index)
            {
                const auto& part = pattern.parts[index];
                hasLiteral |= !part.empty();
                if (part.find_first_of("{}") != std::string::npos ||
                    (index > 0 && index + 1 < pattern.parts.size() && part.empty()))
                    throw std::runtime_error("Invalid localization pattern");
            }
            if (pattern.parts.size() < 2 || !hasLiteral)
                throw std::runtime_error("Invalid localization pattern");
            auto target = pattern.translation;
            for (size_t index = 0; index + 1 < pattern.parts.size(); ++index)
            {
                const auto marker = "{" + std::to_string(index) + "}";
                const auto position = target.find(marker);
                if (position == std::string::npos)
                    throw std::runtime_error("Missing localization capture");
                target.erase(position, marker.size());
            }
            if (target.find_first_of("{}") != std::string::npos)
                throw std::runtime_error("Invalid localization capture");
            patterns.push_back(std::move(pattern));
        }
        enabled = true;
        return true;
    }
    catch (const std::exception&)
    {
        messages.clear();
        patterns.clear();
        return false;
    }
}

inline std::string Translate(std::string_view source)
{
    if (!enabled || source.empty())
        return {};
    const auto found = messages.find(std::string(source));
    if (found != messages.end())
        return found->second;
    for (const auto& pattern : patterns)
    {
        if (source.substr(0, pattern.parts.front().size()) != pattern.parts.front())
            continue;
        size_t position = pattern.parts.front().size();
        std::vector<std::string_view> values;
        bool matched = true;
        for (size_t index = 1; index < pattern.parts.size(); ++index)
        {
            const auto& delimiter = pattern.parts[index];
            const bool last = index + 1 == pattern.parts.size();
            const size_t end = last ? (source.size() >= delimiter.size() ? source.size() - delimiter.size()
                                                                                       : std::string::npos)
                                    : source.find(delimiter, position);
            if (end == std::string::npos || end < position || source.substr(end, delimiter.size()) != delimiter)
            {
                matched = false;
                break;
            }
            values.push_back(source.substr(position, end - position));
            position = end + delimiter.size();
        }
        if (!matched || position != source.size())
            continue;
        std::string result;
        for (size_t offset = 0; offset < pattern.translation.size();)
        {
            bool substituted = false;
            for (size_t index = 0; index < values.size(); ++index)
            {
                const auto marker = "{" + std::to_string(index) + "}";
                if (pattern.translation.compare(offset, marker.size(), marker) == 0)
                {
                    result.append(values[index]);
                    offset += marker.size();
                    substituted = true;
                    break;
                }
            }
            if (!substituted)
                result += pattern.translation[offset++];
        }
        return result;
    }
    return {};
}

class Text
{
    std::string translated;

  public:
    Text(const char*& begin, const char*& end, bool translate = true)
    {
        if (!translate || !begin || begin == end || !enabled || suppressed)
            return;
        translated = Translate(end ? std::string_view(begin, end - begin) : std::string_view(begin));
        if (!translated.empty())
        {
            begin = translated.data();
            end = begin + translated.size();
        }
    }
};
}