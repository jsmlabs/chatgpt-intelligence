"""Local MCP stdio host for the INTEL text generators.

Implements a bounded JSON-RPC 2.0 subset of MCP 2025-11-25 / 2025-06-18:
initialize, notifications/initialized, ping, tools/list, tools/call.
No HTTP listener, filesystem export or implicit model permissions.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from typing import Any, BinaryIO

from .foundation import Authorization, Permission, IntelError
from .model_host import OpenAIResponsesHost
from .ollama_host import OllamaLocalHost
from .provider_router import ProviderRouter
from .text_runtime import TextRuntime
from .host_drafts import submit_host_draft
from .image_runtime import ImageRuntime
from .design_runtime import DesignRuntime
from .theme_runtime import ThemeRuntime
from .brand_runtime import BrandRuntime
from .motion_runtime import MotionRuntime
from .slides_runtime import SlidesRuntime
from .diagram_runtime import DiagramRuntime
from .image_render import render_image
from .comfyui_image import ComfyUIHost

MAX_INPUT_LINE = 131072
SUPPORTED_VERSIONS = frozenset({"2025-06-18", "2025-11-25"})
TOOL_TYPES = {"generate_prompt": "PROMPT", "generate_concept": "CONCEPT",
              "generate_document": "DOCUMENT"}
SUBMIT_TYPES = {"submit_prompt_draft": "PROMPT", "submit_concept_draft": "CONCEPT",
                "submit_document_draft": "DOCUMENT"}
IMAGE_TOOLS = ("generate_image_brief", "submit_image_brief")
DESIGN_TOOL = "generate_design"
THEME_TOOL = "generate_theme"
BRAND_TOOL = "generate_brand"
MOTION_TOOL = "generate_motion"
SLIDES_TOOL = "generate_slides"
DIAGRAM_TOOL = "generate_diagram"
RENDER_TOOL = "render_abstract_image"
COMFY_TOOL = "generate_image_comfyui"
DESCRIPTION = {
    "generate_prompt": "Generate an editable Markdown prompt draft.",
    "generate_concept": "Generate an editable Markdown concept brief.",
    "generate_document": "Generate an editable Markdown document draft.",
    "submit_prompt_draft": "Validate an already-written prompt draft supplied by the ChatGPT client; no model call.",
    "submit_concept_draft": "Validate an already-written concept draft supplied by the ChatGPT client; no model call.",
    "submit_document_draft": "Validate an already-written document draft supplied by the ChatGPT client; no model call.",
    "generate_image_brief": "Generate a deterministic IMAGE production brief; no image file or model call.",
    "submit_image_brief": "Validate a client-written IMAGE production brief; no image file or model call.",
    "render_abstract_image": "Render a small, deterministic procedural geometric PNG. No AI prompt-to-image generation, no model API, no semantic subject rendering.",
    "generate_diagram": "Generate validated directed acyclic diagrams as JSON, Mermaid source or offline SVG; no Mermaid browser/parser claim.",
    "generate_slides": "Generate offline editable PPTX or structured slide storyboard JSON. No remote images or model; PPTX returned as base64 encoded binary in structured content.",
    "generate_motion": "Create deterministic motion storyboard JSON or actual procedural animated GIF89a with verified frames and timing. No semantic scene or external renderer.",
    "generate_brand": "Generate deterministic brand identity brief, reusable JSON theme tokens, or static SVG logo concept. No trademark clearance or image model.",
    "generate_theme": "Create deterministic light/dark JSON design tokens or CSS and audited WCAG 2.2 color-pair contrast results; no full accessibility certification.",
    "generate_design": "Generate deterministic UI/UX design brief or inert responsive HTML/CSS prototype; no browser/app execution.",
    "generate_image_comfyui": "Opt-in local semantic text-to-image generation via installed ComfyUI checkpoint and core nodes. Requires --allow-comfyui-image and CREATE. No cloud or partner nodes.",
}
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "objective": {"type": "string", "minLength": 1, "maxLength": 8192},
        "audience": {"type": "string", "maxLength": 512},
        "style": {"type": "string", "maxLength": 512},
        "sources": {"type": "array", "maxItems": 16, "items": {"type": "string", "maxLength": 1024}},
        "constraints": {"type": "array", "maxItems": 16, "items": {"type": "string", "maxLength": 1024}},
        "verification": {"type": "array", "maxItems": 16, "items": {"type": "string", "maxLength": 1024}},
        "format": {"type": "string", "enum": ["markdown"]},
        "mode": {"type": "string", "enum": ["template", "model"]},
        "provider": {"type": "string", "enum": ["template", "ollama-local",
                                                   "chatgpt-host", "openai-api"]},
    },
    "required": ["objective"],
    "additionalProperties": False,
}

SUBMIT_SCHEMA = {
    "type": "object",
    "properties": {
        **{key: value for key, value in INPUT_SCHEMA["properties"].items()
           if key not in {"mode", "provider"}},
        "content": {"type": "string", "minLength": 1, "maxLength": 65536},
    },
    "required": ["objective", "content"],
    "additionalProperties": False,
}


IMAGE_SCHEMA = {
    "type": "object",
    "properties": {
        **{key: value for key, value in INPUT_SCHEMA["properties"].items()
           if key not in {"provider", "mode"}},
        "aspect_ratio": {"type": "string", "enum": ["1:1", "3:2", "2:3", "4:3", "3:4", "16:9", "9:16"]},
        "palette": {"type": "string", "maxLength": 512},
    },
    "required": ["objective"],
    "additionalProperties": False,
}
IMAGE_SUBMIT_SCHEMA = {
    **IMAGE_SCHEMA,
    "properties": {**IMAGE_SCHEMA["properties"],
                   "content": {"type": "string", "minLength": 1, "maxLength": 65536}},
    "required": ["objective", "content"],
}


RENDER_SCHEMA = {
    "type": "object",
    "properties": {
        "objective": {"type": "string", "minLength": 1, "maxLength": 8192},
        "aspect_ratio": {"type": "string", "enum": ["1:1", "3:2", "2:3", "4:3", "3:4", "16:9", "9:16"]},
        "palette": {"type": "string", "maxLength": 128},
    },
    "required": ["objective"],
    "additionalProperties": False,
}


DESIGN_SCHEMA = {
    "type": "object",
    "properties": {
        **{key: value for key, value in INPUT_SCHEMA["properties"].items()
           if key not in {"mode", "provider"}},
        "format": {"type": "string", "enum": ["markdown", "html"]},
        "layout": {"type": "string", "enum": ["dashboard", "landing", "form", "catalog"]},
        "responsive": {"type": "string", "enum": ["mobile-first", "desktop-first"]},
        "components": {"type": "array", "minItems": 1, "maxItems": 8,
                       "items": {"type": "string", "enum": ["header", "navigation", "hero",
                       "summary", "cards", "filters", "form", "footer"]}},
    },
    "required": ["objective"],
    "additionalProperties": False,
}


THEME_SCHEMA = {
    "type": "object",
    "properties": {
        "objective": {"type": "string", "minLength": 1, "maxLength": 8192},
        "preset": {"type": "string", "enum": ["graphite", "ocean", "plum", "forest"]},
        "accent": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
        "format": {"type": "string", "enum": ["json", "css"]},
    },
    "required": ["objective"],
    "additionalProperties": False,
}


BRAND_SCHEMA = {
    "type": "object",
    "properties": {
        "objective": {"type": "string", "minLength": 1, "maxLength": 8192},
        "name": {"type": "string", "minLength": 1, "maxLength": 96},
        "audience": {"type": "string", "maxLength": 512},
        "style": {"type": "string", "maxLength": 512},
        "values": {"type": "array", "maxItems": 8,
                   "items": {"type": "string", "minLength": 1, "maxLength": 1024}},
        "preset": {"type": "string", "enum": ["graphite", "ocean", "plum", "forest"]},
        "accent": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
        "direction": {"type": "string", "enum": ["orbit", "signal", "aperture"]},
        "format": {"type": "string", "enum": ["markdown", "json", "svg"]},
    },
    "required": ["objective", "name"],
    "additionalProperties": False,
}


MOTION_SCHEMA = {
    "type": "object",
    "properties": {
        "objective": {"type": "string", "minLength": 1, "maxLength": 4096},
        "motion": {"type": "string", "enum": ["pulse", "orbit", "bounce"]},
        "format": {"type": "string", "enum": ["json", "gif"]},
        "width": {"type": "integer", "minimum": 64, "maximum": 256},
        "height": {"type": "integer", "minimum": 64, "maximum": 256},
        "frames": {"type": "integer", "minimum": 2, "maximum": 12},
        "frame_duration_ms": {"type": "integer", "minimum": 50, "maximum": 1000, "multipleOf": 10},
        "loop": {"type": "integer", "minimum": 0, "maximum": 20},
        "preset": {"type": "string", "enum": ["graphite", "ocean", "plum", "forest"]},
        "accent": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
    },
    "required": ["objective"],
    "additionalProperties": False,
}


SLIDES_SCHEMA = {
    "type": "object",
    "properties": {
        "objective": {"type": "string", "minLength": 1, "maxLength": 4096},
        "audience": {"type": "string", "minLength": 1, "maxLength": 240},
        "preset": {"type": "string", "enum": ["graphite", "ocean", "plum", "forest"]},
        "accent": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
        "format": {"type": "string", "enum": ["json", "pptx"]},
        "slides": {
            "type": "array", "minItems": 1, "maxItems": 12,
            "items": {"type": "object", "properties": {
                "layout": {"type": "string", "enum": ["title", "section", "bullets", "two-column"]},
                "title": {"type": "string", "minLength": 1, "maxLength": 160},
                "body": {"type": "array", "maxItems": 6,
                         "items": {"type": "string", "minLength": 1, "maxLength": 220}}},
                "required": ["title"], "additionalProperties": False}},
    },
    "required": ["objective"],
    "additionalProperties": False,
}


DIAGRAM_SCHEMA = {
    "type": "object",
    "properties": {
        "objective": {"type": "string", "minLength": 1, "maxLength": 1024},
        "kind": {"type": "string", "enum": ["flowchart", "architecture"]},
        "direction": {"type": "string", "enum": ["TB", "LR"]},
        "format": {"type": "string", "enum": ["json", "mermaid", "svg"]},
        "preset": {"type": "string", "enum": ["graphite", "ocean", "plum", "forest"]},
        "accent": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
        "nodes": {"type": "array", "minItems": 1, "maxItems": 16,
                  "items": {"type": "object", "properties": {
                      "id": {"type": "string", "pattern": "^[a-z][a-z0-9_]{0,31}$"},
                      "label": {"type": "string", "minLength": 1, "maxLength": 64},
                      "type": {"type": "string", "enum": ["process", "decision", "service", "database"]}},
                      "required": ["id", "label"], "additionalProperties": False}},
        "edges": {"type": "array", "maxItems": 24,
                  "items": {"type": "object", "properties": {
                      "source": {"type": "string"}, "target": {"type": "string"},
                      "label": {"type": "string", "maxLength": 48}},
                      "required": ["source", "target"], "additionalProperties": False}},
    },
    "required": ["objective"],
    "additionalProperties": False,
}


COMFY_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt": {"type": "string", "minLength": 1, "maxLength": 4096},
        "negative_prompt": {"type": "string", "maxLength": 1024},
        "width": {"type": "integer", "minimum": 256, "maximum": 1024},
        "height": {"type": "integer", "minimum": 256, "maximum": 1024},
        "steps": {"type": "integer", "minimum": 1, "maximum": 40},
        "seed": {"type": "integer", "minimum": 0, "maximum": 4294967295},
    },
    "required": ["prompt"],
    "additionalProperties": False,
}


class MCPHost:
    def __init__(self, authorization: Authorization | None = None,
                 model_host: OpenAIResponsesHost | None = None,
                 provider_router: ProviderRouter | None = None,
                 allow_comfyui_image: bool = False,
                 comfyui_host: ComfyUIHost | None = None):
        self.authorization = authorization or Authorization()
        self.runtime = TextRuntime(model_host=model_host, provider_router=provider_router)
        self.image_runtime = ImageRuntime()
        self.design_runtime = DesignRuntime()
        self.theme_runtime = ThemeRuntime()
        self.brand_runtime = BrandRuntime()
        self.motion_runtime = MotionRuntime()
        self.slides_runtime = SlidesRuntime()
        self.diagram_runtime = DiagramRuntime()
        self.allow_comfyui_image = bool(allow_comfyui_image)
        self.comfyui_host = comfyui_host or ComfyUIHost()
        self.initialized = False

    def handle(self, message: Any) -> dict | None:
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            return self._error(None, -32600, "Invalid JSON-RPC request")
        method = message.get("method")
        request_id = message.get("id")
        if isinstance(request_id, (bool, dict, list)) or not (
            request_id is None or isinstance(request_id, (str, int))
        ):
            return self._error(None, -32600, "Invalid JSON-RPC request id")
        if not isinstance(method, str) or "result" in message or "error" in message:
            return self._error(request_id, -32600, "Invalid JSON-RPC method")
        if method == "notifications/initialized" and request_id is None:
            return None
        if request_id is None:
            # Ignore notifications and never execute side effects from them.
            return None
        params = message.get("params", {})
        if not isinstance(params, dict):
            return self._error(request_id, -32602, "Invalid parameters")
        if method == "initialize":
            version = params.get("protocolVersion")
            if version not in SUPPORTED_VERSIONS:
                version = "2025-11-25"
            self.initialized = True
            return self._ok(request_id, {
                "protocolVersion": version, "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "chatgpt-intelligence", "version": "0.11.0"},
            })
        if not self.initialized:
            return self._error(request_id, -32002, "Initialize MCP connection first")
        if method == "ping":
            return self._ok(request_id, {})
        if method == "tools/list":
            return self._ok(request_id, {"tools": [
                {"name": name, "description": DESCRIPTION[name],
                 "inputSchema": INPUT_SCHEMA} for name in TOOL_TYPES
            ] + [
                {"name": name, "description": DESCRIPTION[name],
                 "inputSchema": SUBMIT_SCHEMA,
                 "annotations": {"readOnlyHint": False, "destructiveHint": False,
                                 "idempotentHint": False, "openWorldHint": False}}
                for name in SUBMIT_TYPES
            ] + [
                {"name": name, "description": DESCRIPTION[name],
                 "inputSchema": IMAGE_SUBMIT_SCHEMA if name == "submit_image_brief" else IMAGE_SCHEMA,
                 "annotations": {"readOnlyHint": False, "destructiveHint": False,
                                 "idempotentHint": False, "openWorldHint": False}}
                for name in IMAGE_TOOLS
            ] + [{"name": DIAGRAM_TOOL, "description": DESCRIPTION[DIAGRAM_TOOL],
                  "inputSchema": DIAGRAM_SCHEMA,
                  "annotations": {"readOnlyHint": False, "destructiveHint": False,
                                  "idempotentHint": False, "openWorldHint": False}}
            ] + [{"name": SLIDES_TOOL, "description": DESCRIPTION[SLIDES_TOOL],
                  "inputSchema": SLIDES_SCHEMA,
                  "annotations": {"readOnlyHint": False, "destructiveHint": False,
                                  "idempotentHint": False, "openWorldHint": False}}
            ] + [{"name": MOTION_TOOL, "description": DESCRIPTION[MOTION_TOOL],
                  "inputSchema": MOTION_SCHEMA,
                  "annotations": {"readOnlyHint": False, "destructiveHint": False,
                                  "idempotentHint": False, "openWorldHint": False}}
            ] + [{"name": BRAND_TOOL, "description": DESCRIPTION[BRAND_TOOL],
                  "inputSchema": BRAND_SCHEMA,
                  "annotations": {"readOnlyHint": False, "destructiveHint": False,
                                  "idempotentHint": False, "openWorldHint": False}}
            ] + [{"name": THEME_TOOL, "description": DESCRIPTION[THEME_TOOL],
                  "inputSchema": THEME_SCHEMA,
                  "annotations": {"readOnlyHint": False, "destructiveHint": False,
                                  "idempotentHint": False, "openWorldHint": False}}
            ] + [{"name": DESIGN_TOOL, "description": DESCRIPTION[DESIGN_TOOL],
                  "inputSchema": DESIGN_SCHEMA,
                  "annotations": {"readOnlyHint": False, "destructiveHint": False,
                                  "idempotentHint": False, "openWorldHint": False}}
            ] + [{"name": RENDER_TOOL, "description": DESCRIPTION[RENDER_TOOL],
                  "inputSchema": RENDER_SCHEMA,
                  "annotations": {"readOnlyHint": True, "destructiveHint": False,
                                  "idempotentHint": True, "openWorldHint": False}}] +
                 ([{"name": COMFY_TOOL, "description": DESCRIPTION[COMFY_TOOL],
                    "inputSchema": COMFY_SCHEMA,
                    "annotations": {"readOnlyHint": True, "destructiveHint": False,
                                    "idempotentHint": False, "openWorldHint": False}}]
                  if self.allow_comfyui_image else [])})
        if method == "tools/call":
            name, arguments = params.get("name"), params.get("arguments", {})
            if name not in TOOL_TYPES and name not in SUBMIT_TYPES and name not in IMAGE_TOOLS and name != RENDER_TOOL and name != DESIGN_TOOL and name != THEME_TOOL and name != BRAND_TOOL and name != MOTION_TOOL and name != SLIDES_TOOL and name != DIAGRAM_TOOL and not (self.allow_comfyui_image and name == COMFY_TOOL):
                return self._error(request_id, -32602, "Unknown INTEL tool")
            if not isinstance(arguments, dict):
                return self._error(request_id, -32602, "Tool arguments must be an object")
            if name == COMFY_TOOL:
                if set(arguments) - set(COMFY_SCHEMA["properties"]):
                    return self._error(request_id, -32602, "Unknown ComfyUI field")
                try:
                    self.authorization.require(frozenset({Permission.CREATE}))
                    # Only trusted server startup can authorize local model inference.
                    if not self.allow_comfyui_image:
                        raise IntelError("PERMISSION_DENIED", "Local image inference disabled")
                    image = self.comfyui_host.generate(
                        arguments.get("prompt"),
                        negative_prompt=arguments.get("negative_prompt", ""),
                        width=arguments.get("width", 512),
                        height=arguments.get("height", 512),
                        steps=arguments.get("steps", 20),
                        seed=arguments.get("seed", 0),
                        authorization=Authorization(frozenset({Permission.CREATE, Permission.EXTERNAL})),
                    )
                except IntelError as exc:
                    return self._ok(request_id, {
                        "content": [{"type": "text", "text": json.dumps(
                            {"code": exc.code, "message": exc.message}, sort_keys=True)}],
                        "isError": True})
                return self._ok(request_id, {
                    "content": [{"type": "image", "data": base64.b64encode(image.png).decode("ascii"),
                                 "mimeType": image.mime_type}],
                    "structuredContent": {"capability": "image", "artifact_type": "image/png",
                                          "width": image.width, "height": image.height,
                                          "sha256": image.sha256, "image_generated": True,
                                          "image_verified": True, "model_provider": image.provider,
                                          "model_checkpoint": image.checkpoint, "prompt_id": image.prompt_id,
                                          "output_verified": False, "human_review": "not_run",
                                          "source_verification": "not_run"},
                    "isError": False,
                })
            if name == RENDER_TOOL:
                if set(arguments) - set(RENDER_SCHEMA["properties"]):
                    return self._error(request_id, -32602, "Unknown raster rendering field")
                try:
                    image = render_image(arguments.get("objective"),
                                         aspect_ratio=arguments.get("aspect_ratio", "1:1"),
                                         palette=arguments.get("palette", ""),
                                         authorization=self.authorization)
                except IntelError as exc:
                    return self._ok(request_id, {
                        "content": [{"type": "text", "text": json.dumps(
                            {"code": exc.code, "message": exc.message}, sort_keys=True)}],
                        "isError": True})
                return self._ok(request_id, {
                    "content": [{"type": "image", "data": base64.b64encode(image.png).decode("ascii"),
                                 "mimeType": "image/png"}],
                    "structuredContent": {"capability": "image", "artifact_type": "image/png",
                                          "width": image.width, "height": image.height,
                                          "sha256": image.sha256, "image_generated": True,
                                          "image_verified": True, "model_provider": "not-used",
                                          "producer": image.producer,
                                          "semantic_prompt_followed": False,
                                          "output_verified": False},
                    "isError": False,
                })
            if name == DIAGRAM_TOOL:
                if set(arguments) - set(DIAGRAM_SCHEMA["properties"]):
                    return self._error(request_id, -32602, "Unknown DIAGRAM field")
                result = self.diagram_runtime.execute(
                    "/INTEL GENERATE DIAGRAM", request=arguments,
                    authorization=self.authorization)
            elif name == SLIDES_TOOL:
                if set(arguments) - set(SLIDES_SCHEMA["properties"]):
                    return self._error(request_id, -32602, "Unknown SLIDES field")
                result = self.slides_runtime.execute(
                    "/INTEL GENERATE SLIDES", request=arguments, authorization=self.authorization)
                if result["ok"] and isinstance(result["content"], bytes):
                    return self._ok(request_id, {
                        "content": [{"type": "text", "text": "Editable PPTX generated in memory; see structuredContent.base64."}],
                        "structuredContent": {
                            "capability": "slides",
                            "artifact_type": result["manifest"].artifact_type,
                            "state": result["manifest"].state.value,
                            "output_verified": False,
                            "base64": base64.b64encode(result["content"]).decode("ascii"),
                            "provenance": result["manifest"].provenance,
                            "verification": result["evidence"],
                        }, "isError": False})
            elif name == MOTION_TOOL:
                if set(arguments) - set(MOTION_SCHEMA["properties"]):
                    return self._error(request_id, -32602, "Unknown motion field")
                result = self.motion_runtime.execute(
                    "/INTEL GENERATE GIF", request=arguments, authorization=self.authorization)
                if result["ok"] and isinstance(result["content"], bytes):
                    return self._ok(request_id, {
                        "content": [{"type": "image", "data": base64.b64encode(
                            result["content"]).decode("ascii"), "mimeType": "image/gif"}],
                        "structuredContent": {
                            "capability": "motion", "artifact_type": "image/gif",
                            "state": result["manifest"].state.value,
                            "output_verified": False,
                            "provenance": result["manifest"].provenance,
                            "verification": result["evidence"],
                        }, "isError": False})
            elif name == BRAND_TOOL:
                if set(arguments) - set(BRAND_SCHEMA["properties"]):
                    return self._error(request_id, -32602, "Unknown BRAND field")
                result = self.brand_runtime.execute(
                    "/INTEL GENERATE BRAND", request=arguments, authorization=self.authorization)
            elif name == THEME_TOOL:
                if set(arguments) - set(THEME_SCHEMA["properties"]):
                    return self._error(request_id, -32602, "Unknown THEME field")
                result = self.theme_runtime.execute(
                    "/INTEL GENERATE THEME", request=arguments, authorization=self.authorization)
            elif name == DESIGN_TOOL:
                if set(arguments) - set(DESIGN_SCHEMA["properties"]):
                    return self._error(request_id, -32602, "Unknown DESIGN field")
                result = self.design_runtime.execute(
                    "/INTEL GENERATE DESIGN", request=arguments, authorization=self.authorization)
            elif name in IMAGE_TOOLS:
                schema = IMAGE_SUBMIT_SCHEMA if name == "submit_image_brief" else IMAGE_SCHEMA
                if set(arguments) - set(schema["properties"]):
                    return self._error(request_id, -32602, "Unknown IMAGE field")
                draft = arguments.get("content") if name == "submit_image_brief" else None
                brief = {key: value for key, value in arguments.items() if key != "content"}
                result = self.image_runtime.execute(
                    "/INTEL GENERATE IMAGE", request=brief,
                    authorization=self.authorization, draft=draft)
            elif name in SUBMIT_TYPES:
                if set(arguments) - set(SUBMIT_SCHEMA["properties"]):
                    return self._error(request_id, -32602, "Unknown submission field")
                content = arguments.get("content")
                brief = {key: value for key, value in arguments.items() if key != "content"}
                result = submit_host_draft(
                    SUBMIT_TYPES[name], request=brief, content=content,
                    authorization=self.authorization)
            else:
                mode = arguments.get("mode", "template")
                if not isinstance(mode, str) or mode not in ("template", "model"):
                    return self._error(request_id, -32602, "Invalid execution mode")
                provider = arguments.get("provider")
                brief = {key: value for key, value in arguments.items()
                         if key not in {"mode", "provider"}}
                result = self.runtime.execute(
                    "/INTEL GENERATE " + TOOL_TYPES[name],
                    request=brief, authorization=self.authorization, mode=mode, provider=provider,
                )
            if not result["ok"]:
                error = result["error"]
                return self._ok(request_id, {
                    "content": [{"type": "text", "text": json.dumps(error, sort_keys=True)}],
                    "isError": True,
                })
            manifest = result["manifest"]
            return self._ok(request_id, {
                "content": [{"type": "text", "text": result["content"]}],
                "structuredContent": {
                    "artifact_id": manifest.identifier,
                    "capability": manifest.capability,
                    "version": manifest.version,
                    "state": manifest.state.value,
                    "output_verified": manifest.output_verified,
                    "provenance": manifest.provenance,
                    "verification": result["evidence"],
                },
                "isError": False,
            })
        return self._error(request_id, -32601, "Method not found")

    @staticmethod
    def _ok(request_id: str | int, result: dict) -> dict:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def _error(request_id: str | int | None, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": request_id,
                "error": {"code": code, "message": message}}


def serve(host: MCPHost, source: BinaryIO, sink: BinaryIO) -> None:
    while True:
        line = source.readline(MAX_INPUT_LINE + 1)
        if not line:
            return
        if len(line) > MAX_INPUT_LINE:
            # Drain oversized request without buffering it or evaluating any content.
            while line and not line.endswith(b"\n"):
                line = source.readline(MAX_INPUT_LINE + 1)
            reply = MCPHost._error(None, -32700, "Request exceeds transport size limit")
        else:
            try:
                message = json.loads(line)
            except (UnicodeError, ValueError):
                reply = MCPHost._error(None, -32700, "Invalid JSON")
            else:
                try:
                    reply = host.handle(message)
                except Exception:
                    # Never leak an arbitrary exception, token or source content.
                    reply = MCPHost._error(message.get("id") if isinstance(message, dict)
                                           and isinstance(message.get("id"), (str, int))
                                           else None, -32603, "Internal server error")
        if reply is not None:
            sink.write((json.dumps(reply, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8"))
            sink.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local MCP stdio host for INTEL")
    parser.add_argument("--model-timeout", type=float, default=60.0)
    parser.add_argument("--model-max-output-tokens", type=int, default=4096)
    parser.add_argument("--allow-comfyui-image", action="store_true",
                        help="Operator opt-in to local ComfyUI inference; requires --allow-create and installed checkpoint")
    parser.add_argument("--allow-create", action="store_true",
                        help="Trusted operator grant for draft creation")
    parser.add_argument("--allow-external", action="store_true",
                        help="Trusted operator grant for external service access")
    parser.add_argument("--allow-billable", action="store_true",
                        help="Trusted operator grant for billable model calls")
    args = parser.parse_args(argv)
    granted: set[Permission] = set()
    if args.allow_create:
        granted.add(Permission.CREATE)
    if args.allow_external:
        granted.add(Permission.EXTERNAL)
    if args.allow_billable:
        granted.add(Permission.BILLABLE)
    if not 1 <= args.model_timeout <= 120 or not 128 <= args.model_max_output_tokens <= 8192:
        parser.error("Model timeout must be 1-120 seconds and tokens 128-8192")
    if args.allow_comfyui_image and not args.allow_create:
        parser.error("--allow-comfyui-image requires --allow-create")
    host = MCPHost(Authorization(frozenset(granted)),
                   allow_comfyui_image=args.allow_comfyui_image,
                   provider_router=ProviderRouter(
                       ollama_host=OllamaLocalHost(timeout=args.model_timeout,
                                                   max_output_tokens=args.model_max_output_tokens),
                       openai_host=OpenAIResponsesHost(timeout=args.model_timeout,
                                                       max_output_tokens=args.model_max_output_tokens)))
    serve(host, sys.stdin.buffer, sys.stdout.buffer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
