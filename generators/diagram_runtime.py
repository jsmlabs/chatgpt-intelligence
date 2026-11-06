"""Validated offline DAG diagrams as JSON, Mermaid, or standalone SVG."""
from __future__ import annotations
from collections import deque
from dataclasses import replace
from datetime import datetime, timezone
from html import escape
import hashlib
import json
import os
from pathlib import Path
import re
from uuid import uuid4
from xml.etree import ElementTree as ET
from .artifacts import ArtifactManifest, ArtifactState
from .foundation import Authorization, IntelError, Permission, State, default_registry, parse_command
from .text_runtime import _require_text
from .theme_runtime import PRESETS, hex_color, palette_for

FORMATS = ("json", "mermaid", "svg")
KINDS = ("flowchart", "architecture")
DIRECTIONS = ("TB", "LR")
TYPES = ("process", "decision", "service", "database")
NODE_ID = re.compile(r"[a-z][a-z0-9_]{0,31}\Z")
FILE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.(?:json|mmd|svg)\Z")
SVG = "http://www.w3.org/2000/svg"


def diagram_capability():
    return replace(default_registry().resolve("DIAGRAM"), state=State.AVAILABLE,
                   implemented=True, formats=FORMATS, required_tools=(), risk="low",
                   version="0.1.0", description="Validated offline DAG, Mermaid and SVG")


def text(value, field, length):
    result = _require_text(value, field, required=True, limit=length)
    if any(ord(c) < 32 or ord(c) == 127 for c in result):
        raise IntelError("INVALID_REQUEST", field + " contains control characters")
    return result


def depths(nodes, edges):
    degree = {n["id"]: 0 for n in nodes}
    follow = {n["id"]: [] for n in nodes}
    order = {n["id"]: i for i, n in enumerate(nodes)}
    layer = {n["id"]: 0 for n in nodes}
    for e in edges:
        degree[e["target"]] += 1
        follow[e["source"]].append(e["target"])
    pending = deque(key for key in order if degree[key] == 0)
    visited = 0
    while pending:
        key = pending.popleft()
        visited += 1
        for nxt in sorted(follow[key], key=order.get):
            layer[nxt] = max(layer[nxt], layer[key] + 1)
            degree[nxt] -= 1
            if degree[nxt] == 0:
                pending.append(nxt)
    if visited != len(nodes):
        raise IntelError("INVALID_REQUEST", "Cycles are not supported")
    return layer


def validate(argument, request):
    if request is None:
        request = {}
    allowed = {"objective", "kind", "direction", "format", "preset", "accent", "nodes", "edges"}
    if not isinstance(request, dict) or set(request) - allowed:
        raise IntelError("INVALID_REQUEST", "Unknown diagram fields")
    objective = text(request.get("objective", argument), "objective", 1024)
    kind = text(request.get("kind", "flowchart"), "kind", 32)
    direction = text(request.get("direction", "TB"), "direction", 8)
    fmt = text(request.get("format", "json"), "format", 16)
    preset = text(request.get("preset", "graphite"), "preset", 32)
    if kind not in KINDS or direction not in DIRECTIONS or preset not in PRESETS:
        raise IntelError("INVALID_REQUEST", "Invalid diagram configuration")
    if fmt not in FORMATS:
        raise IntelError("UNSUPPORTED_FORMAT", "Use json, mermaid or svg")
    accent = hex_color(request["accent"]) if "accent" in request else PRESETS[preset]
    nodes, edges = request.get("nodes"), request.get("edges")
    if nodes is None and edges is None:
        nodes = [{"id": "start", "label": "Start"},
                 {"id": "task", "label": objective[:64], "type": "service" if kind == "architecture" else "process"},
                 {"id": "finish", "label": "Review"}]
        edges = [{"source": "start", "target": "task"}, {"source": "task", "target": "finish"}]
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 16:
        raise IntelError("INVALID_REQUEST", "Expected 1..16 nodes")
    if not isinstance(edges, list) or len(edges) > 24:
        raise IntelError("INVALID_REQUEST", "Expected at most 24 edges")
    clean_nodes, known = [], set()
    for n in nodes:
        if not isinstance(n, dict) or set(n) - {"id", "label", "type"}:
            raise IntelError("INVALID_REQUEST", "Invalid node")
        key = text(n.get("id"), "id", 32)
        label = text(n.get("label"), "label", 64)
        kind_of_node = text(n.get("type", "process"), "type", 20)
        if not NODE_ID.fullmatch(key) or key in known or kind_of_node not in TYPES:
            raise IntelError("INVALID_REQUEST", "Invalid node ID or type")
        known.add(key)
        clean_nodes.append({"id": key, "label": label, "type": kind_of_node})
    clean_edges, pairs = [], set()
    for e in edges:
        if not isinstance(e, dict) or set(e) - {"source", "target", "label"}:
            raise IntelError("INVALID_REQUEST", "Invalid edge")
        source = text(e.get("source"), "source", 32)
        target = text(e.get("target"), "target", 32)
        label = e.get("label", "")
        if not isinstance(label, str) or len(label) > 48 or any(ord(c) < 32 for c in label):
            raise IntelError("INVALID_REQUEST", "Invalid edge label")
        if source not in known or target not in known or source == target or (source, target) in pairs:
            raise IntelError("INVALID_REQUEST", "Unknown, self or duplicate edge")
        pairs.add((source, target))
        clean_edges.append({"source": source, "target": target, "label": label})
    depths(clean_nodes, clean_edges)
    return objective, kind, direction, fmt, preset, accent, clean_nodes, clean_edges


def graph_data(objective, kind, direction, preset, accent, nodes, edges):
    layer = depths(nodes, edges)
    slots, coords = {}, {}
    for n in nodes:
        depth = layer[n["id"]]
        slot = slots.get(depth, 0)
        slots[depth] = slot + 1
        coords[n["id"]] = (140 + (slot if direction == "TB" else depth) * 250,
                           95 + (depth if direction == "TB" else slot) * 160)
    colors = palette_for(accent)["light"]
    return {"schema_version": "1.0", "capability": "diagram", "objective": objective,
            "kind": kind, "direction": direction,
            "theme": {"preset": preset, "accent": accent, "background": colors["background"],
                      "surface": colors["surface"], "text": colors["text"],
                      "line": colors["border"], "on_accent": colors["on_accent"]},
            "canvas": {"width": max(p[0] for p in coords.values()) + 150,
                       "height": max(p[1] for p in coords.values()) + 100},
            "nodes": [{**n, "x": coords[n["id"]][0], "y": coords[n["id"]][1],
                       "layer": layer[n["id"]]} for n in nodes],
            "edges": edges, "provenance": {"producer": "local-deterministic-diagram",
                                         "mermaid_parser": "not_run", "visual_review": "not_run"}}


def render_mermaid(data):
    def label(s):
        substitutions = {"&": "#amp;", '"': "#quot;", "<": "#lt;", ">": "#gt;",
                         "#": "#35;", "[": "#91;", "]": "#93;", "|": "#124;",
                         "{": "#123;", "}": "#125;", ";": "#59;"}
        return "".join(substitutions.get(c, c) for c in s)
    output = ["flowchart " + data["direction"]]
    for n in data["nodes"]:
        key, value = n["id"], label(n["label"])
        if n["type"] == "decision":
            shape = key + '{"' + value + '"}'
        elif n["type"] == "database":
            shape = key + '[("' + value + '")]'
        elif n["type"] == "service":
            shape = key + '(["' + value + '"])'
        else:
            shape = key + '["' + value + '"]'
        output.append("    " + shape)
    for e in data["edges"]:
        connector = "-->|" + label(e["label"]) + "|" if e["label"] else "-->"
        output.append("    " + e["source"] + " " + connector + " " + e["target"])
    return "\n".join(output) + "\n"


def render_svg(data):
    theme = data["theme"]
    width, height = data["canvas"]["width"], data["canvas"]["height"]
    nodes = {n["id"]: n for n in data["nodes"]}
    output = ['<svg xmlns="' + SVG + '" viewBox="0 0 ' + str(width) + " " +
              str(height) + '" role="img" aria-labelledby="title desc">',
              '<title id="title">' + escape(data["objective"]) + '</title>',
              '<desc id="desc">Directed acyclic ' + escape(data["kind"]) + '</desc>',
              '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">'
              '<path d="M0 0 L6 3 L0 6 Z" fill="' + theme["line"] + '"/></marker></defs>',
              '<rect width="100%" height="100%" fill="' + theme["background"] + '"/>']
    for edge in data["edges"]:
        a, b = nodes[edge["source"]], nodes[edge["target"]]
        if data["direction"] == "TB":
            start, end = (a["x"], a["y"] + 35), (b["x"], b["y"] - 35)
        else:
            start, end = (a["x"] + 94, a["y"]), (b["x"] - 94, b["y"])
        output.append('<path d="M' + str(start[0]) + " " + str(start[1]) +
                      " L" + str(end[0]) + " " + str(end[1]) +
                      '" stroke="' + theme["line"] + '" fill="none" stroke-width="2" marker-end="url(#arrow)"/>')
        if edge["label"]:
            output.append('<text x="' + str((start[0]+end[0])//2) + '" y="' +
                          str((start[1]+end[1])//2-8) + '" font-size="12" text-anchor="middle" fill="' +
                          theme["text"] + '">' + escape(edge["label"]) + '</text>')
    for n in data["nodes"]:
        x, y = n["x"], n["y"]
        fill = theme["accent"] if n["type"] == "decision" else theme["surface"]
        ink = theme["on_accent"] if n["type"] == "decision" else theme["text"]
        if n["type"] == "decision":
            output.append('<polygon points="' + f"{x},{y-38} {x+94},{y} {x},{y+38} {x-94},{y}" +
                          '" fill="' + fill + '"/>')
        else:
            output.append('<rect x="' + str(x-94) + '" y="' + str(y-35) +
                          '" width="188" height="70" rx="' + ("28" if n["type"] == "service" else "8") +
                          '" fill="' + fill + '" stroke="' + theme["line"] + '"/>')
        output.append('<text x="' + str(x) + '" y="' + str(y+5) +
                      '" text-anchor="middle" font-size="14" font-family="system-ui,sans-serif" fill="' +
                      ink + '">' + escape(n["label"]) + '</text>')
    return "\n".join(output + ["</svg>\n"])


def verify_svg(svg, data):
    try:
        root = ET.fromstring(svg)
        elements = list(root.iter())
        labels = [n.text or "" for n in root.findall(".//{" + SVG + "}text")]
        return {"xml_valid": root.tag == "{" + SVG + "}svg",
                "elements_allowlisted": all(n.tag.removeprefix("{" + SVG + "}") in {
                    "svg", "title", "desc", "defs", "marker", "path", "rect", "polygon", "text"
                } for n in elements),
                "node_texts": all(n["label"] in labels for n in data["nodes"]),
                "edge_texts": all(e["label"] in labels for e in data["edges"] if e["label"]),
                "no_external": not re.search(r"<script\b|<foreignObject\b|<!DOCTYPE|<!ENTITY|"
                                             r"\b(?:href|src)\s*=|@import|javascript:", svg, re.I)}
    except ET.ParseError:
        return {"xml_valid": False}


def export_diagram(content, root, filename, fmt):
    suffix = "mmd" if fmt == "mermaid" else fmt
    if not isinstance(filename, str) or not FILE.fullmatch(filename) or not filename.endswith("." + suffix):
        raise IntelError("INVALID_PATH", "Plain filename and matching extension required")
    if not isinstance(root, Path) or not root.is_dir() or root.is_symlink():
        raise IntelError("INVALID_PATH", "Export root must be an existing directory")
    path = root.resolve(strict=True) / filename
    payload = content.encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        with os.fdopen(os.open(path, flags, 0o600), "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if path.read_bytes() != payload:
            raise IntelError("EXPORT_UNVERIFIED", "Readback differs from source")
    except FileExistsError:
        raise IntelError("DESTINATION_EXISTS", "Refusing to overwrite existing file") from None
    except OSError:
        raise IntelError("EXPORT_FAILED", "Diagram export failed") from None
    return filename, hashlib.sha256(payload).hexdigest()


class DiagramRuntime:
    def __init__(self):
        self.capability = diagram_capability()

    def execute(self, raw, *, request=None, authorization=None, export_root=None,
                filename=None, mode="template", provider=None):
        manifest = None
        try:
            command = parse_command(raw)
            if command.name != "GENERATE" or command.generator != "DIAGRAM":
                raise IntelError("INVALID_COMMAND", "Expected /INTEL GENERATE DIAGRAM")
            objective, kind, direction, fmt, preset, accent, nodes, edges = validate(
                command.argument, request)
            (authorization or Authorization()).require(frozenset({Permission.CREATE}))
            if provider not in (None, "template") or mode != "template":
                raise IntelError("CAPABILITY_UNAVAILABLE", "Only deterministic local diagrams supported")
            if (export_root is None) != (filename is None):
                raise IntelError("INVALID_REQUEST", "Export requires root and filename")
            data = graph_data(objective, kind, direction, preset, accent, nodes, edges)
            content = (json.dumps(data, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
                       if fmt == "json" else render_mermaid(data) if fmt == "mermaid"
                       else render_svg(data))
            manifest = ArtifactManifest(uuid4().hex, {
                "json": "application/json", "mermaid": "text/vnd.mermaid", "svg": "image/svg+xml"
            }[fmt], "1.0", (), "diagram")
            manifest.created_at = datetime.now(timezone.utc).isoformat()
            manifest.provenance = {"producer": "local-deterministic-diagram",
                                   "model_provider": "not-used", "source_status": "unverified",
                                   "renderer_version": self.capability.version}
            manifest.transition(ArtifactState.READY)
            manifest.transition(ArtifactState.GENERATING)
            manifest.transition(ArtifactState.VALIDATING)
            checks = {"bounded": 0 < len(content.encode("utf-8")) <= 65536}
            if fmt == "json":
                checks["roundtrip"] = json.loads(content) == data
            elif fmt == "mermaid":
                checks["source"] = content == render_mermaid(data)
            else:
                checks.update(verify_svg(content, data))
            manifest.validations = checks
            if not all(checks.values()):
                raise IntelError("VALIDATION_FAILED", "Diagram structure failed validation")
            manifest.transition(ArtifactState.REVIEWED)
            evidence = {"structural_validation": "passed", "node_count": len(nodes),
                        "edge_count": len(edges), "acyclic": True, "format": fmt,
                        "svg_xml_verified": fmt == "svg",
                        "mermaid_parser": "not_run", "browser_render": "not_run",
                        "visual_review": "not_run", "source_verification": "not_run"}
            if export_root is not None:
                name, digest = export_diagram(content, export_root, filename, fmt)
                manifest.record_verified_output(name, export_root)
                manifest.transition(ArtifactState.EXPORTED, output_verified=True)
                evidence["file_sha256"] = digest
            return {"ok": True, "capability": "diagram", "content": content,
                    "manifest": manifest, "evidence": evidence, "verified": False}
        except IntelError as exc:
            if manifest is not None and manifest.state not in (ArtifactState.FAILED, ArtifactState.EXPORTED):
                manifest.transition(ArtifactState.FAILED)
            return {**exc.as_result(), "manifest": manifest}
