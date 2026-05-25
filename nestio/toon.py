from .base import BaseStorage


def _encode_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    if "," in s or "\n" in s or s.startswith('"'):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def _decode_value(s: str):
    s = s.strip()
    if s == "null":
        return None
    if s == "true":
        return True
    if s == "false":
        return False
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1].replace('\\"', '"')
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def _split_csv_row(line: str) -> list:
    fields = []
    current = []
    in_quotes = False
    i = 0
    while i < len(line):
        c = line[i]
        if c == '"' and not in_quotes:
            in_quotes = True
        elif c == '"' and in_quotes:
            if i + 1 < len(line) and line[i + 1] == '"':
                current.append('"')
                i += 1
            else:
                in_quotes = False
        elif c == "," and not in_quotes:
            fields.append("".join(current))
            current = []
        else:
            current.append(c)
        i += 1
    fields.append("".join(current))
    return fields


def _dumps(data, indent: int = 0) -> list[str]:
    lines = []
    prefix = "  " * indent

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.extend(_dumps(value, indent + 1))
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                fields = list(value[0].keys())
                header = f"{prefix}{key}[{len(value)}]{{{','.join(fields)}}}:"
                lines.append(header)
                for item in value:
                    row_vals = [_encode_value(item.get(f)) for f in fields]
                    lines.append(f"{prefix}  {','.join(row_vals)}")
            elif isinstance(value, list):
                encoded = [_encode_value(v) for v in value]
                lines.append(f"{prefix}{key}[{len(value)}]: {','.join(encoded)}")
            else:
                lines.append(f"{prefix}{key}: {_encode_value(value)}")
    return lines


def dumps(data: dict) -> str:
    return "\n".join(_dumps(data)) + "\n"


def loads(text: str) -> dict:
    lines = text.splitlines()
    result, _ = _parse_block(lines, 0, 0)
    return result


def _get_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_block(lines: list[str], start: int, base_indent: int) -> tuple[dict, int]:
    result = {}
    i = start

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        indent = _get_indent(line)

        if indent < base_indent:
            break

        stripped = line.strip()

        # Tabular array: key[N]{fields}:
        if "{" in stripped and "}" in stripped and stripped.endswith(":"):
            bracket_start = stripped.index("[")
            bracket_end = stripped.index("]")
            brace_start = stripped.index("{")
            brace_end = stripped.index("}")
            key = stripped[:bracket_start]
            count = int(stripped[bracket_start + 1:bracket_end])
            fields = stripped[brace_start + 1:brace_end].split(",")
            rows = []
            i += 1
            while i < len(lines) and len(rows) < count:
                row_line = lines[i]
                if not row_line.strip():
                    i += 1
                    continue
                if _get_indent(row_line) <= indent:
                    break
                vals = _split_csv_row(row_line.strip())
                obj = {f: _decode_value(v) for f, v in zip(fields, vals)}
                rows.append(obj)
                i += 1
            result[key] = rows
            continue

        # Primitive array: key[N]: val1,val2,...
        if "[" in stripped and "]" in stripped and ":" in stripped:
            bracket_start = stripped.index("[")
            bracket_end = stripped.index("]")
            colon_pos = stripped.index(":", bracket_end)
            key = stripped[:bracket_start]
            raw_vals = stripped[colon_pos + 1:].strip()
            vals = _split_csv_row(raw_vals) if raw_vals else []
            result[key] = [_decode_value(v) for v in vals]
            i += 1
            continue

        # Nested object: key:  (nothing after colon, or just whitespace)
        if stripped.endswith(":") and ":" == stripped[-1]:
            key = stripped[:-1].strip()
            i += 1
            if i < len(lines) and _get_indent(lines[i]) > indent:
                child, i = _parse_block(lines, i, indent + 1)
                result[key] = child
            else:
                result[key] = {}
            continue

        # Scalar: key: value
        if ": " in stripped or stripped.endswith(":"):
            colon_pos = stripped.index(":")
            key = stripped[:colon_pos].strip()
            value_str = stripped[colon_pos + 1:].strip()
            result[key] = _decode_value(value_str)
            i += 1
            continue

        i += 1

    return result, i


class Toon(BaseStorage):
    def __init__(self, path: str):
        super().__init__(path)

    def _serialize(self, data: dict) -> str:
        return dumps(data)

    def _deserialize(self, text: str) -> dict:
        return loads(text)
