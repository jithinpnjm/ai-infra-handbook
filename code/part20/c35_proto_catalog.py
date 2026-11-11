"""List services, methods and long-running operations from .proto text.

A tiny, purpose-built parser, not a full protobuf grammar. It strips comments,
finds `service X { ... }` blocks with brace matching, and reads each `rpc` line.
A method is long-running when its response type is the Operation message of
nebius.common.v1 or nebius.common.v1alpha1 (the API README: mutating methods return an Operation).
Standard library only.
"""
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ENDPOINT_SUFFIX = ".api.nebius.cloud:443"
_OPERATION_NAMES = {
    "Operation",
    "common.v1.Operation", "nebius.common.v1.Operation",
    "common.v1alpha1.Operation", "nebius.common.v1alpha1.Operation",
}
_COMMON_PACKAGES = {"nebius.common.v1", "nebius.common.v1alpha1"}

_RPC = re.compile(
    r"\brpc\s+(\w+)\s*\(\s*(stream\s+)?([\w.]+)\s*\)\s*returns\s*\(\s*(stream\s+)?([\w.]+)\s*\)"
)
_PACKAGE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.M)
_SERVICE = re.compile(r"\bservice\s+(\w+)\s*\{")
_API_NAME = re.compile(r'option\s*\(\s*api_service_name\s*\)\s*=\s*"([^"]*)"')


@dataclass
class Method:
    name: str
    request: str
    response: str
    long_running: bool
    streaming: bool


@dataclass
class Service:
    package: str
    name: str
    api_service_name: str = ""
    methods: list = field(default_factory=list)

    @property
    def full_name(self):
        return f"{self.package}.{self.name}"

    @property
    def endpoint(self):
        """Endpoint host:port, or '' when the service has no standalone endpoint."""
        return self.api_service_name + ENDPOINT_SUFFIX if self.api_service_name else ""

    @property
    def long_running(self):
        return [m for m in self.methods if m.long_running]


def strip_comments(text):
    """Remove // and /* */ comments, leaving string literals intact."""
    out, i, n = [], 0, len(text)
    while i < n:
        two = text[i:i + 2]
        if text[i] == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            out.append(text[i:j + 1])
            i = j + 1
        elif two == "//":
            while i < n and text[i] != "\n":
                i += 1
        elif two == "/*":
            end = text.find("*/", i + 2)
            i = n if end < 0 else end + 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _block(text, open_idx):
    """Return the text inside the brace opened at open_idx (strings already safe)."""
    depth, i = 0, open_idx
    while i < len(text):
        c = text[i]
        if c == '"':
            i += 1
            while i < len(text) and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[open_idx + 1:i]
        i += 1
    raise ValueError("unbalanced braces in service block")


def is_operation(response_type, package):
    if response_type in _OPERATION_NAMES:
        # a bare "Operation" only means the common one inside nebius.common.v1
        return response_type != "Operation" or package in _COMMON_PACKAGES
    return False


def parse_proto(text):
    clean = strip_comments(text)
    pm = _PACKAGE.search(clean)
    package = pm.group(1) if pm else ""
    services = []
    for sm in _SERVICE.finditer(clean):
        body = _block(clean, sm.end() - 1)
        svc = Service(package=package, name=sm.group(1))
        # OperationService.Get returns an Operation but only reads one that exists.
        reads_operation_only = svc.name == "OperationService" and package in _COMMON_PACKAGES
        am = _API_NAME.search(body)
        if am:
            svc.api_service_name = am.group(1)
        for rm in _RPC.finditer(body):
            name, req_stream, req, resp_stream, resp = rm.groups()
            svc.methods.append(Method(
                name=name, request=req, response=resp,
                long_running=reads_operation_only is False and is_operation(resp, package),
                streaming=bool(req_stream or resp_stream),
            ))
        services.append(svc)
    return services


def parse_files(paths):
    result = []
    for p in sorted(paths):
        result.extend(parse_proto(Path(p).read_text(encoding="utf-8")))
    return result


def render(services):
    lines = []
    for s in services:
        lro = len(s.long_running)
        lines.append(f"{s.full_name}  endpoint={s.endpoint or '(none: use the initiating service)'}"
                     f"  methods={len(s.methods)} long_running={lro}")
        for m in s.methods:
            tag = "LRO " if m.long_running else "    "
            lines.append(f"  {tag}{m.name}({m.request}) -> {m.response}")
    return "\n".join(lines)


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "c35_fixtures"
    print(render(parse_files(root.rglob("*.proto"))))
