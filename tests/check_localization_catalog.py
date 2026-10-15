#!/usr/bin/env python3
"""Read-only, stdlib lexical audit of first-party UI text (not C++ reachability).

Run: python3 tests/check_localization_catalog.py --report /tmp/localization-audit.json
     python3 tests/check_localization_catalog.py --self-test

Reads the catalog ONCE; reports its SHA256. No preprocessing: every #if branch is
retained. Direct display arguments and reviewed UI producer families are evidence,
not proof that a widget is reachable in a particular build. Unknown expressions,
concatenation fragments and unclassified APIs remain explicit review items. Never
use the stale-candidate list as an automatic deletion list. In particular a catalog
key can be assembled without any identical source literal.
"""

import argparse
from bisect import bisect_right
import hashlib
import itertools
import json
import re
import string
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path


# Comments/characters are tokens too, so quotes in them cannot become UI strings.
TOKEN = re.compile(
    r'(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)|'
    r'(?P<raw>(?:u8|u|U|L)?R"(?P<delimiter>[^ ()\\\t\r\n]{0,16})\([\s\S]*?\)(?P=delimiter)")|'
    r'(?P<string>(?:u8|u|U|L)?"(?:\\[\s\S]|[^"\\])*")|'
    r"(?P<char>(?:u8|u|U|L)?'(?:\\[\s\S]|[^'\\])*')|"
    r'(?P<word>[A-Za-z_]\w*)|(?P<other>[^\s])'
)
PRINTF = re.compile(r'%(?:\d+\$)?[-+ #0\']*(?:\d+|\*(?:\d+\$)?)?'
                    r'(?:\.(?:\d+|\*(?:\d+\$)?))?(?:I64|I32|hh|ll|[hljztL])?[diuoxXfFeEgGaAcspn]')
CAPTURE = '\ue000'


@dataclass
class Token:
    value: str
    start: int
    end: int
    line: int
    text: str | None = None


def decode_literal(value):
    """Decode C++ escapes without corrupting UTF-8 as unicode_escape would."""
    if re.match(r'^(?:u8|u|U|L)?R"', value):
        begin = value.index('(')
        delimiter = value[value.index('R"') + 2:begin]
        return value[begin + 1:-(len(delimiter) + 2)]
    body = value[value.index('"') + 1:-1]
    escapes = {'n': '\n', 'r': '\r', 't': '\t', 'a': '\a', 'b': '\b',
               'f': '\f', 'v': '\v', '\\': '\\', '"': '"', "'": "'", '?': '?'}

    def replace(match):
        item = match.group(1)
        if item == '\n':
            return ''
        if item.startswith(('x', 'u', 'U')):
            return chr(int(item[1:], 16))
        if item[0] in '01234567':
            return chr(int(item, 8))
        return escapes.get(item, '\\' + item)

    return re.sub(r'\\(x[0-9a-fA-F]+|u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|[0-7]{1,3}|[\s\S])', replace, body)


def lex(source):
    result = []
    newlines = [match.start() for match in re.finditer('\n', source)]
    for match in TOKEN.finditer(source):
        kind = match.lastgroup
        if kind == 'comment':
            continue
        value = match.group()
        text = decode_literal(value) if kind in ('string', 'raw') else None
        token = Token(value, match.start(), match.end(), bisect_right(newlines, match.start()) + 1, text)
        if text is not None and result and result[-1].text is not None:
            result[-1].text += text
            result[-1].end = token.end
        else:
            result.append(token)
    return result


def pairs(tokens):
    stack, result = [], {}
    for i, token in enumerate(tokens):
        if token.value in ('(', '[', '{') and token.text is None:
            stack.append(i)
        elif token.value in (')', ']', '}') and token.text is None:
            if stack and tokens[stack[-1]].value == {')': '(', ']': '[', '}': '{'}[token.value]:
                start = stack.pop()
                result[start] = i
    return result


def split(tokens, separator=','):
    groups, start, depth = [], 0, 0
    for i, token in enumerate(tokens):
        if token.text is not None:
            continue
        if token.value in ('(', '[', '{'):
            depth += 1
        elif token.value in (')', ']', '}'):
            depth -= 1
        elif token.value == separator and depth == 0:
            groups.append(tokens[start:i])
            start = i + 1
    return groups + [tokens[start:]]


def printf_template(text):
    text = text.replace('%%', '\ue001')
    text = PRINTF.sub(CAPTURE, text)
    return text.replace('\ue001', '%')


def format_template(text):
    try:
        return ''.join(literal + (CAPTURE if field is not None else '')
                       for literal, field, _, _ in string.Formatter().parse(text))
    except ValueError:
        return None


def numbered(text):
    count = itertools.count()
    return re.sub(CAPTURE, lambda _: '{' + str(next(count)) + '}', text)


def expression(tokens):
    """Small expression subset; None means unknown, never empty/non-displayed."""
    if not tokens:
        return None
    matching = pairs(tokens)
    if tokens[0].value == '(' and matching.get(0) == len(tokens) - 1:
        return expression(tokens[1:-1])
    # A conditional's condition is deliberately not interpreted.
    depth, question, nested = 0, None, 0
    for i, token in enumerate(tokens):
        if token.text is not None:
            continue
        if token.value in ('(', '[', '{'):
            depth += 1
        elif token.value in (')', ']', '}'):
            depth -= 1
        elif depth == 0 and token.value == '?':
            if question is None:
                question = i
            else:
                nested += 1
        elif depth == 0 and token.value == ':' and question is not None:
            if nested:
                nested -= 1
            else:
                left, right = expression(tokens[question + 1:i]), expression(tokens[i + 1:])
                return None if left is None or right is None else left + right
    chunks = split(tokens, '+')
    if len(chunks) > 1:
        values = [expression(chunk) for chunk in chunks]
        if not any(value is not None for value in values):
            return None
        return [''.join(parts) for parts in itertools.islice(
            itertools.product(*(value if value is not None else [CAPTURE] for value in values)), 64)]
    if len(tokens) == 1 and tokens[0].text is not None:
        return [tokens[0].text]
    values = ''.join(t.value for t in tokens)
    if values.endswith('.c_str()'):
        return expression(tokens[:-4])
    for i, token in enumerate(tokens):
        if token.value != '(' or i == 0:
            continue
        name = ''.join(t.value for t in tokens[:i])
        end = matching.get(i)
        if end != len(tokens) - 1:
            continue
        args = split(tokens[i + 1:end])
        if name in ('std::string', 'std::string_view'):
            return expression(args[0])
        if name in ('std::format', 'StrFmt'):
            source = expression(args[0])
            if source is not None:
                convert = format_template if name == 'std::format' else printf_template
                converted = [convert(text) for text in source]
                return None if None in converted else converted
    return None


# Explicit, reviewed text arguments. IDs, URLs, format/value arguments are NOT labels.
LABEL_APIS = set('Button SmallButton Checkbox CheckboxFlags RadioButton Selectable '
                 'CollapsingHeader TreeNode TreeNodeEx SeparatorText TextLink TextLinkOpenURL '
                 'BeginMenu MenuItem BeginTabItem TableSetupColumn InputText InputTextMultiline '
                 'InputTextWithHint SliderFloat SliderInt SliderScalar SliderFloat2 SliderFloat3 '
                 'SliderFloat4 SliderInt2 SliderInt3 SliderInt4 DragFloat DragInt InputFloat InputInt '
                 'InputDouble InputScalar VSliderFloat ColorEdit3 ColorEdit4 ColorPicker3 ColorPicker4 '
                 'PlotLines PlotHistogram'.split())
FORMAT_ARGUMENTS = {name: 4 for name in ('SliderFloat', 'SliderFloat2', 'SliderFloat3', 'SliderFloat4',
                                         'SliderInt', 'SliderInt2', 'SliderInt3', 'SliderInt4',
                                         'InputFloat', 'InputDouble')}
FORMAT_ARGUMENTS.update({name: 5 for name in ('SliderScalar', 'VSliderFloat', 'DragFloat', 'DragInt', 'InputScalar')})
HELPERS = {'ShowTooltip': [0], 'ShowHelpMarker': [0], 'HelpMarker': [0],
           'SeparatorWithHelpMarker': [0, 1], 'ScopedCollapsingHeader': [0],
           'PopulateCombo': [0], 'AddResourceBarrier': [0], 'AddDLSSRenderPreset': [0],
           'AddDLSSDRenderPreset': [0], 'ShowResetButton': [1], 'CheckboxWrapped': [0],
           'DeferredSlider': [0], 'Slider': [0], 'slider': [0], 'Checkbox': [0],
           'tool': [0], 'showHelp': [0], 'drawTag': [0]}
UI_FILES = {'menu_common.cpp', 'menu_common.h', 'DlssNr_Menu.cpp', 'DlssNr_MenuControls.cpp',
            'DlssNr_MenuSections.h', 'DlssNr_PipelineUi.h', 'DlssNr_MenuOverlay.cpp'}
# Reviewed non-UI producers feeding NR status text. These are not generic log sinks.
STATUS_CALLS = {'DlssNrFeature_Vk.cpp': {'Fail': [0], 'PublishStatus': [2]},
                'DlssNrFeature_Vk_Model.cpp': {'Fail': [0]},
                'DlssNrFinished_Vk.cpp': {'Say': [0]},
                'DlssNr_Dx12_DeferredSr.cpp': {'Say': [0]},
                'DlssNr_Dx12_Enlarge.cpp': {'say': [0]},
                'DlssNr_Dx12_Late.cpp': {'Say': [0]},
                'DlssNr_Dx12_FinishedQueue.cpp': {'Say': [0]},
                'DlssNr_Dx12_FinishedCompose.cpp': {'Say': [0]},
                'DlssNr_Dx12_Evaluate.cpp': {'Say': [0]}}
STATUS_FIELDS = {'DlssNrFeature_Vk.cpp': {'spatialStatus'},
                 'DlssNrFeature_Vk_Model.cpp': {'spatialStatus'},
                 'DlssNrFinished_Vk.cpp': {'status'},
                 'DlssNr_Dx12_Run.cpp': {'reason', 'enlargementStatus', 'spatialFallbackReason'},
                 'DlssNr_Dx12_Models.cpp': {'reason', 'spatialFallbackReason'},
                 'DlssNr_Dx12_FinishedQueue.cpp': {'enlargementStatus'},
                 'DlssNr_Dx12_State.h': {'status'},
                 'DlssNr_Dx12_Status.cpp': {'spatialStatus'},
                 'DlssNr_Spatial.h': {'reason'}}
# Every string literal in these initializer families is rendered as an option or
# tooltip. Pure enum/resource/vendor names are subsequently classified separately.
PRODUCER_ARRAYS = {'menu_common.cpp': {'splashText', 'presets', 'inputOptions', 'outputOptions',
                                      'nvngxOptions', 'lfx_modes', 'reflex_modes', 'lowLatencyInput',
                                      'lowLatencyOutput', 'lowlatency_states', 'ds_options',
                                      'common_flags', 'uncommon_flags', 'debug_flags'},
                   'DlssNr_PipelineUi.h': {'names', 'labels'}}
TECHNICAL = re.compile(r'^(?:[A-Z][A-Z0-9]*_[A-Z0-9_]+|PRESET [A-Z]|[A-Z]|\(?[0-9.]+[xX%]?\)?|'
                       r'(?:DLSS|FSR|XeSS|XeFG|DLSSG|D3D|DX|Vulkan)[0-9. +xX|()/-]*)$')
TECHNICAL_LABELS = {'Lanczos', 'Kaiser', 'Bicubic', 'Catmull-Rom', 'scRGB', 'Reflex', 'XeLL',
                    'UeLowLatency', 'AntiLag 2', 'AntiLag Vk', "Nukem's", 'Opti', 'fakenvapi',
                    'LatencyFlex', 'Kaiser2', 'Kaiser3', 'Lanczos2', 'Lanczos3', 'FSR 3/4 FG', 'FSR FG',
                    'KPSS', 'SPLAT', 'MFG', 'MAGIC', 'DLAA', 'HDR', 'RCAS', 'COMMON', 'PRESENT', 'PREDICATION'}


def nonlinguistic(text):
    stripped = re.sub(r'\{\d+\}', '', text).strip()
    units_only = re.sub(r'\b(?:ms|fps|px|MB|GB|Hz|x)\b', '', stripped, flags=re.IGNORECASE)
    return (not re.search(r'[A-Za-z\u0080-\uffff]', units_only) or stripped in TECHNICAL_LABELS
            or bool(TECHNICAL.fullmatch(stripped)))


def pattern_parts(source):
    parts, start, index = [], 0, 0
    while True:
        marker = '{' + str(index) + '}'
        at = source.find(marker, start)
        if at < 0:
            parts.append(source[start:])
            break
        parts.append(source[start:at])
        start, index = at + len(marker), index + 1
    if (len(parts) < 2 or not any(parts) or any('{' in p or '}' in p for p in parts)
            or any(not p for p in parts[1:-1])):
        raise ValueError('Invalid localization pattern: ' + source)
    return parts


def pattern_captures(parts, source):
    """Exactly Localization.h's ordered delimiter search (NOT greedy regex)."""
    if not source.startswith(parts[0]):
        return None
    position, captures = len(parts[0]), []
    for i, delimiter in enumerate(parts[1:], 1):
        end = len(source) - len(delimiter) if i == len(parts) - 1 else source.find(delimiter, position)
        if end < position or source[end:end + len(delimiter)] != delimiter:
            return None
        captures.append(source[position:end])
        position = end + len(delimiter)
    return captures if position == len(source) else None


def pattern_matches(parts, source):
    return pattern_captures(parts, source) is not None


class Audit:
    def __init__(self):
        self.evidence, self.unresolved, self.fragments, self.unclassified = [], [], [], []
        self.literals = {}
        self.files = []

    def emit(self, path, token, texts, kind, call, confidence='display_argument'):
        for text in texts or []:
            if not text:
                continue
            if call == 'splashText':
                text = printf_template(text)
            # DeferredDlssStatus is inserted into this format, not translated
            # independently. Spatial fallback reasons likewise carry a prefix.
            if (Path(path).name == 'DlssNr_Dx12_DeferredSr.cpp' and call == 'Say') or (
                    Path(path).name == 'DlssNr_Dx12_State.h' and call == 'status' and text == 'not started'):
                text = 'Private upscale: ' + text
            elif call == 'spatialFallbackReason':
                text = 'Fallback to ordinary NR: ' + text
            for item in text.split('\0'):
                item = item.split('##', 1)[0]
                dynamic = CAPTURE in item
                item = numbered(item)
                if item:
                    self.evidence.append({'source': item, 'dynamic': dynamic, 'path': path, 'line': token.line,
                                          'kind': kind, 'call': call, 'confidence': confidence,
                                          'nonlinguistic': nonlinguistic(item)})

    def scan(self, path, source):
        self.files.append(path)
        tokens = lex(source)
        basename = Path(path).name
        ui = basename in UI_FILES
        uses, sink_identifiers = [], set()
        for token in tokens:
            if token.text is not None:
                self.literals.setdefault(token.text, []).append({'path': path, 'line': token.line})
        if (not ui and basename not in STATUS_CALLS and basename not in STATUS_FIELDS
                and not any(marker in source for marker in ('ImGui::', '.setTitle(', '.setContent('))):
            return
        matching = pairs(tokens)
        for i, token in enumerate(tokens):
            if token.value != '(' or i == 0 or i not in matching:
                continue
            name = tokens[i - 1].value
            is_imgui = i >= 4 and ''.join(t.value for t in tokens[i - 4:i - 1]) == 'ImGui::'
            args = split(tokens[i + 1:matching[i]])
            # Reviewed return producer: platform key names are external, but these
            # two fallback strings are first-party UI. No generic return mining.
            body = matching[i] + 1
            if (ui and name == 'KeyNameFromVirtualKeyCode' and body in matching
                    and tokens[body].value == '{'):
                for n in range(body + 1, matching[body]):
                    if tokens[n].value == 'return':
                        end = n + 1
                        while end < matching[body] and tokens[end].value != ';':
                            end += 1
                        self.emit(path, tokens[n], expression(tokens[n + 1:end]), 'reviewed_return', name,
                                  'reviewed_producer')
            indices, formatted, kind = [], False, 'literal'
            if is_imgui:
                if name in LABEL_APIS:
                    indices = [0, 1] if name == 'InputTextWithHint' else [0]
                    if name in FORMAT_ARGUMENTS:
                        indices.append(FORMAT_ARGUMENTS[name])
                elif name in ('Text', 'TextDisabled', 'TextWrapped', 'TextUnformatted', 'SetTooltip', 'SetItemTooltip'):
                    indices, formatted = [0], name != 'TextUnformatted'
                elif name == 'TextColored':
                    indices, formatted = [1], True
                elif name in ('Combo', 'ListBox'):
                    indices = [0, 2]
                elif name == 'BeginCombo':
                    indices = [0, 1]
                elif name == 'SeparatorTextEx':
                    indices = [1]
                elif name == 'ProgressBar':
                    indices = [2]
                elif name == 'InsertNotification':
                    # Initializer-list toast contains only type, duration, content.
                    indices, kind = [0], 'notification'
                elif name in ('Begin', 'BeginPopupModal'):
                    # NoTitleBar overlay windows have an ID, not visible title text.
                    if not any(t.value in ('ImGuiWindowFlags_NoTitleBar', 'ImGuiWindowFlags_NoDecoration')
                               for t in tokens[i:matching[i]]):
                        indices = [0]
            elif i >= 2 and tokens[i - 2].value == 'ImGuiToast':
                indices, kind = [0], 'notification'
            elif ui and name == 'AddText':
                # Reviewed ImDrawList overloads: (position,color,text,...) or
                # (font,size,position,color,text,...). Not CalcTextSize.
                indices, kind = [4 if len(args) >= 5 else 2], 'draw_list'
            elif ui and (name == 'Keybind' or (i >= 2 and tokens[i - 2].value == 'Keybind')):
                indices, kind = [0], 'keybind_constructor'
            elif name in ('setTitle', 'setContent'):
                indices, formatted, kind = [0], True, 'notification'
            elif ui and name in HELPERS:
                indices, kind = HELPERS[name], 'reviewed_helper'
            elif name in STATUS_CALLS.get(basename, {}):
                indices, kind = STATUS_CALLS[basename][name], 'reviewed_status'
            elif ui and name == 'set_disabled':
                indices, kind = [1], 'option_tooltip'
            # Helper declarations are not calls with unknown runtime text.
            if (not is_imgui and indices and args and not any(t.text is not None for t in args[0])
                    and not any(t.value == '(' for t in args[0])
                    and any(t.value in ('const', 'char', 'std', 'ConfigValue', 'CustomOptional') for t in args[0])):
                continue
            if is_imgui and not indices and name not in {
                    'PushID', 'GetID', 'CalcTextSize', 'FindRenderedTextEnd', 'InvisibleButton',
                    'BeginPopup', 'OpenPopup', 'BeginTable', 'BeginChild', 'Begin',
                    'SetClipboardText', 'SetWindowFocus'}:
                for arg in args:
                    for part in arg:
                        if part.text:
                            self.unclassified.append({'path': path, 'line': part.line, 'call': name,
                                                      'literal': part.text, 'reason': 'unclassified API text argument'})
            for index in indices:
                if index >= len(args) or not args[index]:
                    continue
                arg = args[index]
                if kind == 'notification' and arg[0].value == '{':
                    fields = split(arg[1:-1])
                    arg = fields[2] if len(fields) > 2 else arg
                    formatted = True
                elif name == 'PublishStatus' and arg[0].value == '{':
                    # StatusSnapshot.failureReason is field 1, not a log/config key.
                    fields = split(arg[1:-1])
                    arg = fields[1] if len(fields) > 1 else arg
                is_format = formatted or (is_imgui and index == FORMAT_ARGUMENTS.get(name))
                texts = expression(arg)
                if texts is not None:
                    if is_format:
                        texts = [printf_template(text) for text in texts]
                    self.emit(path, arg[0], texts, kind, name)
                else:
                    uses.append((arg, name, kind))
                    sink_identifiers.update(t.value for t in arg if re.fullmatch(r'[A-Za-z_]\w*', t.value))
                # Literal string values passed to %s are semantically uncertain:
                # runtime translates the assembled whole, not each substring.
                if is_format:
                    for extra in args[index + 1:]:
                        for part in extra:
                            if part.text:
                                self.fragments.append({'source': part.text, 'path': path, 'line': part.line,
                                                       'format_sources': [numbered(text) for text in texts or []],
                                                       'reason': 'formatted value, not independently translated'})

        # Conservative producer evidence, no arbitrary source substring liveness.
        producers, mutated = {}, set()
        for i, token in enumerate(tokens):
            if token.value != '=' or i == 0:
                continue
            end = i + 1
            while end < len(tokens) and tokens[end].value != ';':
                if end in matching:
                    end = matching[end] + 1
                else:
                    end += 1
            rhs = tokens[i + 1:end]
            before = tokens[max(0, i - 15):i]
            if len(before) > 1 and before[-1].value in ('+', '-'):
                mutated.add(before[-2].value)
                continue
            # Arrays have a closing ]; scalar/member assignments have a word.
            if before and before[-1].value == ']':
                opens = [n for n, t in enumerate(before) if t.value == '[']
                name = before[opens[-1] - 1].value if opens else ''
            else:
                name = before[-1].value if before else ''
            array = bool(rhs and rhs[0].value == '{')
            reviewed = name in PRODUCER_ARRAYS.get(basename, set())
            status = name in STATUS_FIELDS.get(basename, set())
            # MenuOption label/tooltip fields are known rendered members.
            member = ui and name in ('label', 'tooltip') and any(t.value == '.' for t in before[-3:])
            if (reviewed or (ui and array and name in sink_identifiers)) and array:
                fields = rhs[1:-1]
                for group in split(fields):
                    if group and group[0].value == '{':
                        for field in split(group[1:-1]):
                            texts = expression(field)
                            if texts:
                                self.emit(path, field[0], texts, 'reviewed_array', name, 'reviewed_producer')
                    else:
                        texts = expression(group)
                        if texts:
                            self.emit(path, group[0], texts, 'option_array', name, 'reviewed_producer')
            elif status or member:
                texts = expression(rhs)
                self.emit(path, token, texts, 'reviewed_status' if status else 'option_field', name,
                          'reviewed_producer')
                if texts is None and any(t.text for t in rhs):
                    self.fragments.extend({'source': t.text, 'path': path, 'line': t.line,
                                           'reason': 'unresolved reviewed producer'} for t in rhs if t.text)
            if name and not array:
                texts = expression(rhs)
                if texts:
                    producers.setdefault(name, []).append((token, texts))
        for arg, name, kind in uses:
            values = ''.join(t.value for t in arg)
            variable = re.fullmatch(r'(\w+)(?:\.c_str\(\))?', values)
            bindings = producers.get(variable[1], []) if variable else []
            preceding = [(token, texts) for token, texts in bindings if token.start < arg[0].start]
            inferred = len(preceding) == 1 and variable[1] not in mutated
            if inferred:
                token, texts = preceding[0]
                self.emit(path, token, texts, 'local_initializer', name, 'inferred_local_not_scope_proven')
            self.unresolved.append({'path': path, 'line': arg[0].line, 'call': name,
                                    'expression': source[arg[0].start:arg[-1].end],
                                    'local_candidate_found': inferred,
                                    'reason': 'C++ expression/array/return value requires producer review'})


def load_catalog(raw):
    def unique_object(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate catalog key: ' + key)
            result[key] = value
        return result

    document = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(document, dict):
        raise ValueError('Catalog must be an object')
    messages, patterns = document.get('messages'), document.get('patterns')
    if not isinstance(messages, dict) or not all(isinstance(v, str) and v for v in messages.values()):
        raise ValueError('messages must contain nonempty string translations')
    if not isinstance(patterns, list):
        raise ValueError('patterns must be an array')
    sources = set()
    for entry in patterns:
        if not isinstance(entry, dict) or not all(isinstance(entry.get(k), str) and entry[k]
                                                  for k in ('source', 'target')):
            raise ValueError('Pattern source and target must be nonempty strings')
        if entry['source'] in sources:
            raise ValueError('Duplicate pattern source: ' + entry['source'])
        sources.add(entry['source'])
    return document


def make_report(root, catalog, raw):
    document = load_catalog(raw)
    messages = document['messages']
    patterns, errors = [], []
    for entry in document['patterns']:
        try:
            parts = pattern_parts(entry['source'])
            target = entry['target']
            for i in range(len(parts) - 1):
                marker = '{' + str(i) + '}'
                if marker not in target:
                    raise ValueError('Missing localization capture: ' + entry['source'])
                target = target.replace(marker, '', 1)
            if '{' in target or '}' in target:
                raise ValueError('Invalid localization target: ' + entry['source'])
            patterns.append((entry['source'], parts))
        except ValueError as error:
            errors.append(str(error))
    audit = Audit()
    encoding_notes = []
    for path in sorted((root / 'OptiScaler').rglob('*')):
        if path.suffix not in ('.cpp', '.h', '.hpp') or any(p in ('include', 'external') for p in path.relative_to(root).parts):
            continue
        data = path.read_bytes()
        try:
            source = data.decode('utf-8-sig')
        except UnicodeDecodeError:
            # Legacy Windows source comments occur in this tree. Record fallback;
            # never silently drop bytes or turn decode failures into missing UI.
            source = data.decode('cp1252')
            encoding_notes.append({'path': path.relative_to(root).as_posix(), 'encoding': 'cp1252'})
        audit.scan(path.relative_to(root).as_posix(), source)
    used_messages, used_patterns, gaps, excluded, passthrough = set(), set(), {}, {}, []
    dynamic_review = []
    for item in audit.evidence:
        text = item['source']
        if text in messages and not item['dynamic']:
            used_messages.add(text)
            item['coverage'] = 'exact_message'
        else:
            matches = [source for source, parts in patterns if pattern_matches(parts, text)]
            if matches:
                used_patterns.add(matches[0])
                item['coverage'] = 'template_pattern_candidate' if item['dynamic'] else 'ordered_pattern_literal'
                item['pattern'] = matches[0]
                captures = pattern_captures(next(parts for source, parts in patterns if source == matches[0]), text)
                linguistic = [value for value in captures if not nonlinguistic(value)]
                if linguistic:
                    passthrough.append({'source': text, 'pattern': matches[0], 'captures': linguistic,
                                        'path': item['path'], 'line': item['line'],
                                        'reason': 'Runtime preserves captures verbatim; these English words are not translated by this match.'})
            else:
                specialized = [source for source, _ in patterns
                               if item['dynamic'] and _template_matches(text, source)]
                if specialized and not item['nonlinguistic']:
                    item['coverage'] = 'specialized_runtime_variants_need_review'
                    item['specialized_pattern_candidates'] = specialized
                    dynamic_review.append(item)
                else:
                    item['coverage'] = 'uncovered_template_candidate' if item['dynamic'] else 'uncovered_literal'
                    dest = excluded if item['nonlinguistic'] else gaps
                    dest.setdefault(text, []).append(item)
    stale_messages, uncertain = [], []
    for text in messages:
        if text in used_messages:
            continue
        possible = [item for item in audit.evidence if item['dynamic']
                    and _template_matches(item['source'], text)]
        lexical = audit.literals.get(text, [])
        fragments = [f for f in audit.fragments if f['source'] == text]
        item = {'source': text, 'literal_evidence': lexical, 'fragment_evidence': fragments,
                'possible_dynamic_templates': possible,
                'status': 'not_observed_at_reviewed_display_sink' if lexical or fragments or possible
                else 'no_complete_literal_or_reviewed_template_evidence',
                'deletion_safe': False}
        (uncertain if lexical or fragments or possible else stale_messages).append(item)
    stale_patterns, uncertain_patterns = [], []
    for source, _ in patterns:
        if source in used_patterns:
            continue
        compatible = [item for item in audit.evidence
                      if item['dynamic'] and _template_matches(item['source'], source)]
        entry = {'source': source, 'deletion_safe': False, 'compatible_dynamic_templates': compatible,
                 'reason': 'not directly matched; specialized variants and unresolved outputs may still use it'}
        (uncertain_patterns if compatible else stale_patterns).append(entry)
    return {
        'catalog': str(catalog), 'catalog_sha256': hashlib.sha256(raw).hexdigest(),
        'limitations': ['Lexical audit, not a preprocessed AST or full static UI reachability analysis.',
                        'All conditional compilation branches retained; technical names are review exclusions, not translation requirements.',
                        'Unknown arrays, callback returns, external/user strings and scope-ambiguous locals remain unresolved.',
                        'Template-pattern matches are structural candidates, not proof for every possible runtime capture.',
                        'Generic templates can have specialized runtime patterns; those remain separate coverage-review items.',
                        'Catalog patterns are tried in array order after exact messages, using Localization.h delimiter semantics.',
                        'Stale candidates are NOT safe deletions. Complete strings can be assembled dynamically.'],
        'summary': {'files_scanned': len(audit.files), 'catalog_messages': len(messages),
                    'catalog_patterns': len(document['patterns']), 'display_evidence': len(audit.evidence),
                    'unique_linguistic_gaps': len(gaps),
                    'literal_gap_candidates': sum(any(not e['dynamic'] for e in entries) for entries in gaps.values()),
                    'normalized_template_gap_candidates': sum(all(e['dynamic'] for e in entries) for entries in gaps.values()),
                    'dynamic_template_coverage_review': len(dynamic_review),
                    'unique_nontext_exclusions': len(excluded),
                    'stale_message_candidates': len(stale_messages), 'unobserved_messages_needing_review': len(uncertain),
                    'unobserved_pattern_candidates': len(stale_patterns),
                    'unobserved_patterns_needing_review': len(uncertain_patterns),
                    'unresolved_display_expressions': len(audit.unresolved),
                    'unclassified_api_literals': len(audit.unclassified),
                    'linguistic_capture_passthrough_evidence': len(passthrough), 'catalog_errors': len(errors)},
        'gaps': [{'source': text,
                  'status': 'normalized_template_candidate' if all(e['dynamic'] for e in evidence) else 'literal_gap_candidate',
                  'evidence': evidence} for text, evidence in sorted(gaps.items())],
        'dynamic_template_coverage_review': dynamic_review,
        'stale_message_candidates': stale_messages, 'unobserved_messages_needing_review': uncertain,
        'unobserved_pattern_candidates': stale_patterns, 'unobserved_patterns_needing_review': uncertain_patterns,
        'nontext_exclusions': excluded,
        'unresolved_display_expressions': audit.unresolved, 'formatted_value_fragments': audit.fragments,
        'catalog_errors': errors, 'source_encoding_fallbacks': encoding_notes,
        'unclassified_api_literals': audit.unclassified, 'linguistic_capture_passthrough': passthrough,
        'evidence': audit.evidence,
        'producer_review_notes': [
            'menu_common.cpp: PopulateCombo renders MenuOption.label, tooltip, overrides and set_disabled reasons; stored[] is configuration-only.',
            'menu_common.cpp: splashText is passed as a printf format; Keybind constructor name is a button label.',
            'DlssNr_PipelineUi.h: SectionName names[] and labels[].title/detail feed SeparatorText and draw-list AddText, including ternaries and concatenations.',
            'DlssNr_Menu.cpp/Controls.cpp: failureReason, spatialStatus and FinishedPictureStatus/FinishedVkStatus are rendered with %s; DeferredDlssStatus is prefixed Private upscale: .',
            'DlssNr_Dx12_Status.cpp: Publish forwards nr.reason/enlargementStatus and spatialStatus; DeferredDlssStatus/FinishedPictureStatus return stored context status.',
            'DlssNr_Dx12_DeferredSr.cpp, Late.cpp, FinishedCompose.cpp, FinishedQueue.cpp, Evaluate.cpp, Enlarge.cpp: Say/say store rendered status, not just logs.',
            'DlssNrFeature_Vk*.cpp and DlssNrFinished_Vk.cpp: Fail/Say and spatialStatus feed the NR status UI; DlssNr_Spatial.h reasons also feed Vulkan spatialStatus.',
            'Notifications: InsertNotification initializer content, ImGuiToast constructor content and setTitle/setContent are display evidence; assembled toastMsg remains unresolved.',
            'Resource/engine/model identifiers, profile filenames and hardware/driver values remain technical or external data, not automatic requirements.',
        ],
    }


def _template_matches(template, text):
    try:
        return pattern_matches(pattern_parts(template), text)
    except ValueError:
        return False


class RegressionTests(unittest.TestCase):
    def test_cpp_literals(self):
        tokens = lex('// "ignored"\n"Hello " /* "no" */ "world\\n"; R"x(a\\b)x"; "Centre →";')
        self.assertEqual([t.text for t in tokens if t.text is not None], ['Hello world\n', 'a\\b', 'Centre →'])

    def test_normalization(self):
        self.assertEqual(numbered(printf_template('Value %04d %.2f %% %llu')), 'Value {0} {1} % {2}')
        self.assertEqual(numbered(format_template('Pass {} / {:.2f} {{ok}}')), 'Pass {0} / {1} {ok}')
        self.assertEqual(expression(lex('std::format("Pass {}", n).c_str()')), ['Pass ' + CAPTURE])
        self.assertEqual(expression(lex('flag ? "On" : "Off"')), ['On', 'Off'])

    def test_display_sinks_and_branches(self):
        audit = Audit()
        audit.scan('OptiScaler/menu/menu_common.cpp', '''
            LOG_INFO("Not UI"); config->Set("ConfigOnly");
            #if FEATURE
            ImGui::Button("Save " "Settings##id");
            #else
            ShowTooltip("Conditional help");
            #endif
            const char* options[] = {"Option one", "Option two"};
            const char* stored[] = {"ConfigOnly"};
            ImGui::Combo("Choose", &v, options, 2);
            ImGui::PushID("Not UI ID");
            ImGui::TextColored(color, "Value %d", 1);
            ImGui::InsertNotification({ImGuiToastType::Error, 100, "Oops"});
        ''')
        sources = {e['source'] for e in audit.evidence}
        self.assertTrue({'Save Settings', 'Conditional help', 'Option one', 'Option two', 'Choose', 'Value {0}', 'Oops'} <= sources)
        self.assertFalse({'ConfigOnly', 'Not UI', 'Not UI ID'} & sources)

    def test_helpers_formats_notifications_and_mutation(self):
        audit = Audit()
        audit.scan('OptiScaler/menu/menu_common.cpp', '''
            void ShowTooltip(const char* tip);
            ImGui::SliderFloat("Size", &v, 0, 10, "%.1f%% of screen");
            ImGui::InputTextWithHint("Name", "Type a name", buf, 10);
            draw->AddText(pos, color, "Chart title");
            draw->AddText(font, size, pos, color, "Chart detail", nullptr, wrap);
            auto binding = Keybind("Neural Rendering", 14);
            ImGuiToast notification({Type::Warning, 100, "Visible notification"});
            std::string message = "Header";
            message += filename;
            ImGui::TextUnformatted(message.c_str());
            const char* splashText[] = {"100%% works"};
            std::string KeyNameFromVirtualKeyCode(int key) {
                if (key) return "Unbound";
                return "Unknown";
            }
        ''')
        sources = {e['source'] for e in audit.evidence}
        self.assertTrue({'{0}% of screen', 'Type a name', 'Chart title', 'Chart detail',
                         'Neural Rendering', 'Visible notification', '100% works', 'Unbound', 'Unknown'} <= sources)
        self.assertNotIn('Header', sources)
        self.assertFalse(any('const char' in u['expression'] for u in audit.unresolved))
        self.assertFalse(nonlinguistic('FSR settings'))
        self.assertTrue(nonlinguistic('FSR 3.1'))
        self.assertFalse(nonlinguistic('ON'))
        self.assertFalse(nonlinguistic('AUTO'))

    def test_status_producers_and_prefixes(self):
        audit = Audit()
        audit.scan('OptiScaler/dlssnr/DlssNrFeature_Vk.cpp', '''
            PublishStatus(this, Backend::Vulkan, {false, "Use DX12."});
            LOG_INFO("Not displayed");
        ''')
        audit.scan('OptiScaler/shaders/dlssnr/DlssNr_Dx12_DeferredSr.cpp', 'Say("Not ready.");')
        audit.scan('OptiScaler/shaders/dlssnr/DlssNr_Dx12_Run.cpp',
                   'nr.spatialFallbackReason = "packing failed";')
        sources = {e['source'] for e in audit.evidence}
        self.assertEqual(sources, {'Use DX12.', 'Private upscale: Not ready.',
                                   'Fallback to ordinary NR: packing failed'})
        self.assertEqual(pattern_captures(pattern_parts('Private upscale: {0}'),
                                          'Private upscale: Not ready.'), ['Not ready.'])

    def test_report_dynamic_coverage_is_not_exact_message_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'OptiScaler/menu').mkdir(parents=True)
            (root / 'OptiScaler/menu/menu_common.cpp').write_text('''
                ImGui::Text("Running%s - %.2f ms elapsed%s", mode, elapsed, suffix);
                ImGui::Text("Value %d", count);
            ''', encoding='utf-8')
            catalog = {'messages': {'Value {0}': '值 {0}'}, 'patterns': [
                {'source': 'Running natively on Vulkan - {0} ms elapsed', 'target': '运行 {0} 毫秒'},
            ]}
            report = make_report(root, root / 'catalog.json', json.dumps(catalog).encode())
        self.assertEqual([e['source'] for e in report['dynamic_template_coverage_review']],
                         ['Running{0} - {1} ms elapsed{2}'])
        self.assertEqual(report['summary']['unobserved_patterns_needing_review'], 1)
        self.assertEqual(report['summary']['unobserved_pattern_candidates'], 0)
        self.assertEqual(report['gaps'][0]['source'], 'Value {0}')
        self.assertEqual(report['gaps'][0]['status'], 'normalized_template_candidate')
        self.assertNotEqual(report['gaps'][0]['evidence'][0]['coverage'], 'exact_message')

    def test_catalog_structure(self):
        valid = {'messages': {'Label': '标签'}, 'patterns': [{'source': 'A{0}', 'target': '甲{0}'}]}
        self.assertEqual(load_catalog(json.dumps(valid)), valid)
        for raw in ('[]', '{"messages": {"A": "甲", "A": "乙"}, "patterns": []}',
                    '{"messages": {"A": 1}, "patterns": []}',
                    '{"messages": {"A": ""}, "patterns": []}',
                    '{"messages": {}, "patterns": {}}',
                    '{"messages": {}, "patterns": [{"source": "A{0}"}]}'):
            with self.assertRaises(ValueError):
                load_catalog(raw)
        valid['patterns'].append(valid['patterns'][0])
        with self.assertRaises(ValueError):
            load_catalog(json.dumps(valid))

    def test_runtime_pattern_semantics(self):
        self.assertTrue(pattern_matches(pattern_parts('A{0}B{1}C'), 'AxByC'))
        self.assertFalse(pattern_matches(pattern_parts('A{0}B{1}C'), 'AxByD'))
        # Runtime takes the first internal delimiter, it does not regex-backtrack.
        self.assertFalse(pattern_matches(pattern_parts('A{0}B{1}C{2}D'), 'AxBbadBgoodCvalueDextraCend'))
        for invalid in ('{0}', '{0}{1}x', 'A{1}', 'A{0}{2}'):
            with self.assertRaises(ValueError):
                pattern_parts(invalid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--catalog', type=Path, default=Path('OptiScaler/locales/zh-CN.json'))
    parser.add_argument('--report', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(RegressionTests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    root = args.root.resolve()
    catalog = args.catalog if args.catalog.is_absolute() else root / args.catalog
    raw = catalog.read_bytes()  # Single immutable snapshot, never reread during scan.
    report = make_report(root, catalog, raw)
    if args.report:
        output = args.report.resolve()
        if output == catalog.resolve() or output.suffix != '.json':
            parser.error('--report must be a JSON report, not the input catalog')
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('Report:', output)
    print(json.dumps(report['summary'], ensure_ascii=False, indent=2))
    for item in report['gaps'][:20]:
        evidence = item['evidence'][0]
        print(f"GAP {evidence['path']}:{evidence['line']}: {item['source']!r}")
    return 1 if report['catalog_errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
