"""G3.2 offline PPTX/JSON slide generator using bounded standard-library OOXML.

Exports editable text boxes and geometric surfaces, not rendered images.
No macros, outside relationships, scripts, remote assets or new dependencies.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
from typing import Mapping
from uuid import uuid4
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED, BadZipFile

from .artifacts import ArtifactManifest, ArtifactState
from .foundation import Authorization, IntelError, Permission, State, default_registry, parse_command
from .text_runtime import _require_text
from .theme_runtime import PRESETS, palette_for, hex_color, audit

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
LAYOUTS = ("title", "section", "bullets", "two-column")
FORMATS = ("json", "pptx")
MAX_SLIDES = 12
MAX_BYTES = 250_000
FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.(?:pptx|json)\Z")
SLIDE_W, SLIDE_H = 12192000, 6858000  # 16:9, EMU
EXPECTED_STATIC = frozenset({
    "[Content_Types].xml", "_rels/.rels",
    "docProps/core.xml", "docProps/app.xml",
    "ppt/presentation.xml", "ppt/_rels/presentation.xml.rels",
    "ppt/slideMasters/slideMaster1.xml",
    "ppt/slideMasters/_rels/slideMaster1.xml.rels",
    "ppt/slideLayouts/slideLayout1.xml",
    "ppt/slideLayouts/_rels/slideLayout1.xml.rels",
    "ppt/theme/theme1.xml",
})


def slide_capability():
    return replace(default_registry().resolve("SLIDES"), implemented=True,
                   state=State.AVAILABLE, formats=FORMATS, required_tools=(),
                   risk="low", version="0.1.0",
                   description="Local structured slide outlines and editable PPTX export")


def _text(value, field, maximum=240):
    result = _require_text(value, field, required=True, limit=maximum)
    if any(ord(c) < 32 or ord(c) == 127 for c in result):
        raise IntelError("INVALID_REQUEST", f"{field} contains control characters")
    return result


def request_slides(argument: str, request: Mapping | None):
    if request is None:
        request = {}
    if not isinstance(request, Mapping) or set(request) - {
        "objective", "audience", "preset", "accent", "format", "slides",
    }:
        raise IntelError("INVALID_REQUEST", "Unknown SLIDES request field")
    objective = _text(request.get("objective", argument), "objective", 4096)
    audience = _text(request.get("audience", "General audience"), "audience", 240)
    preset = _text(request.get("preset", "graphite"), "preset", 32)
    fmt = _text(request.get("format", "json"), "format", 16)
    if preset not in PRESETS:
        raise IntelError("INVALID_REQUEST", "Unknown theme preset")
    if fmt not in FORMATS:
        raise IntelError("UNSUPPORTED_FORMAT", "SLIDES supports json or pptx")
    accent = hex_color(request["accent"]) if "accent" in request else PRESETS[preset]
    raw = request.get("slides")
    if raw is None:
        slides = [
            {"layout": "title", "title": objective, "body": [audience]},
            {"layout": "section", "title": "Context", "body": ["Objective and audience"]},
            {"layout": "bullets", "title": "Key points", "body": [
                "Replace these placeholders with verified content.",
                "Review narrative and evidence before publication.",
                "Validate presentation rendering in the target application.",
            ]},
        ]
    else:
        if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_SLIDES:
            raise IntelError("INVALID_REQUEST", "slides must be an array of 1..12 objects")
        slides = []
        for index, item in enumerate(raw):
            if not isinstance(item, Mapping) or set(item) - {"layout", "title", "body"}:
                raise IntelError("INVALID_REQUEST", f"Invalid slide {index} structure")
            layout = _text(item.get("layout", "bullets"), "layout", 32)
            if layout not in LAYOUTS:
                raise IntelError("INVALID_REQUEST", f"Unsupported layout on slide {index}")
            title = _text(item.get("title"), "title", 160)
            body = item.get("body", [])
            if not isinstance(body, list) or len(body) > 6:
                raise IntelError("INVALID_REQUEST", "Slide body requires at most six strings")
            parts = [_text(part, "body item", 220) for part in body]
            if layout == "two-column" and len(parts) < 2:
                raise IntelError("INVALID_REQUEST", "Two-column layout needs at least two items")
            slides.append({"layout": layout, "title": title, "body": parts})
    return objective, audience, preset, accent, fmt, slides


def story_data(objective, audience, preset, accent, slides):
    palette = palette_for(accent)
    contrast = audit(palette)
    if not contrast["aa_passed"]:
        raise IntelError("CONTRAST_FAILED", "Selected theme did not pass audited color pairs")
    return {
        "schema_version": "1.0", "capability": "slides",
        "objective": objective, "audience": audience,
        "canvas": {"width_emu": SLIDE_W, "height_emu": SLIDE_H,
                   "aspect_ratio": "16:9"},
        "theme": {"preset": preset, "accent": accent,
                  "light": palette["light"], "dark": palette["dark"],
                  "contrast_audit": contrast},
        "slides": [{"index": i + 1, **slide} for i, slide in enumerate(slides)],
        "provenance": {"producer": "local-deterministic-ooxml",
                       "model_provider": "not-used", "source_verification": "not_run",
                       "visual_review": "not_run", "powerpoint_open_test": "not_run"},
    }


def _xml_text(value):
    return escape(value, {'"': '&quot;', "'": '&apos;'})


def _tx_shape(identifier, name, text, x, y, w, h, font_size, color, bold=False):
    safe = _xml_text(text)
    return (
        '<p:sp><p:nvSpPr><p:cNvPr id="' + str(identifier) + '" name="' + name +
        '"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr>'
        '<a:xfrm><a:off x="' + str(x) + '" y="' + str(y) +
        '"/><a:ext cx="' + str(w) + '" cy="' + str(h) +
        '"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        '<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        '<p:txBody><a:bodyPr wrap="square"/><a:lstStyle/><a:p>'
        '<a:pPr algn="l"/><a:r><a:rPr lang="en-US" sz="' + str(font_size) +
        '"' + (' b="1"' if bold else '') +
        '><a:solidFill><a:srgbClr val="' + color + '"/></a:solidFill>'
        '</a:rPr><a:t>' + safe + '</a:t></a:r>'
        '<a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>'
    )


def _rect(identifier, name, x, y, w, h, fill):
    return ('<p:sp><p:nvSpPr><p:cNvPr id="' + str(identifier) + '" name="' +
            name + '"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm>'
            '<a:off x="' + str(x) + '" y="' + str(y) + '"/><a:ext cx="' +
            str(w) + '" cy="' + str(h) +
            '"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            '<a:solidFill><a:srgbClr val="' + fill + '"/></a:solidFill>'
            '<a:ln><a:noFill/></a:ln></p:spPr></p:sp>')


def _slide_xml(slide, index, palette):
    bg = palette["background"][1:]
    fg = palette["text"][1:]
    accent = palette["accent"][1:]
    shapes = [_rect(2, "Accent rail", 0, 0, 120000, SLIDE_H, accent)]
    shapes.append(_tx_shape(3, "Title", slide["title"], 640000, 600000,
                            10800000, 1300000, 3600 if slide["layout"] != "title" else 4800,
                            fg, True))
    if slide["layout"] == "two-column":
        for i, item in enumerate(slide["body"]):
            col = i % 2
            row = i // 2
            shapes.append(_tx_shape(4+i, "Column "+str(i+1), item,
                650000 + col * 5650000, 2150000 + row * 1220000,
                4900000, 1000000, 2200, fg))
    else:
        for i, item in enumerate(slide["body"]):
            label = ("• " if slide["layout"] == "bullets" else "") + item
            shapes.append(_tx_shape(4+i, "Body "+str(i+1), label,
                850000, 2200000 + i * 650000,
                10400000, 590000, 1900 if slide["layout"] == "bullets" else 2300, fg))
    shapes.append(_tx_shape(20, "Slide number", str(index), 11100000,
                            6380000, 550000, 300000, 1100, fg))
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sld xmlns:p="' + P + '" xmlns:a="' + A + '" xmlns:r="' + R +
        '"><p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="' +
        bg + '"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>'
        '<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name="Slide shapes"/>'
        '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr>'
        '<a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
        '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm>'
        '</p:grpSpPr>' + "".join(shapes) +
        '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
    ).encode("utf-8")


def _relationships(items):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="' + PR + '">' +
            ''.join('<Relationship Id="rId' + str(i) + '" Type="' + typ +
                    '" Target="' + target + '"/>' for i, typ, target in items) +
            '</Relationships>').encode("utf-8")


def _package(story):
    slides = story["slides"]
    typ = R
    package = {}
    package["_rels/.rels"] = _relationships([
        (1, typ + "/officeDocument", "ppt/presentation.xml"),
        (2, "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
         "docProps/core.xml"),
        (3, typ + "/extended-properties", "docProps/app.xml"),
    ])
    content_types = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    for i in range(1, len(slides) + 1):
        content_types.append('<Override PartName="/ppt/slides/slide' + str(i) +
                             '.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
    package["[Content_Types].xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="' + CT + '">' + ''.join(content_types) + '</Types>').encode()
    ids = ''.join('<p:sldId id="' + str(255+i) + '" r:id="rId' + str(i+1) + '"/>'
                  for i in range(1, len(slides)+1))
    package["ppt/presentation.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:presentation xmlns:p="' + P + '" xmlns:a="' + A + '" xmlns:r="' + R + '">'
        '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
        '<p:sldIdLst>' + ids + '</p:sldIdLst>'
        '<p:sldSz cx="' + str(SLIDE_W) + '" cy="' + str(SLIDE_H) + '" type="screen16x9"/>'
        '<p:notesSz cx="6858000" cy="9144000"/></p:presentation>').encode()
    package["ppt/_rels/presentation.xml.rels"] = _relationships([
        (1, typ + "/slideMaster", "slideMasters/slideMaster1.xml"),
        *[(i+1, typ + "/slide", "slides/slide" + str(i) + ".xml")
          for i in range(1, len(slides)+1)],
    ])
    package["ppt/slideMasters/slideMaster1.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sldMaster xmlns:p="' + P + '" xmlns:a="' + A + '" xmlns:r="' + R + '">'
        '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name="Master"/>'
        '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm>'
        '<a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
        '<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>'
        '<p:clrMap accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4"'
        ' accent5="accent5" accent6="accent6" bg1="lt1" bg2="lt2" folHlink="folHlink"'
        ' hlink="hlink" tx1="dk1" tx2="dk2"/>'
        '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
        '<p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>').encode()
    package["ppt/slideMasters/_rels/slideMaster1.xml.rels"] = _relationships([
        (1, typ + "/slideLayout", "../slideLayouts/slideLayout1.xml"),
        (2, typ + "/theme", "../theme/theme1.xml"),
    ])
    package["ppt/slideLayouts/slideLayout1.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sldLayout xmlns:p="' + P + '" xmlns:a="' + A + '" xmlns:r="' + R +
        '" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree>'
        '<p:nvGrpSpPr><p:cNvPr id="1" name="Layout"/><p:cNvGrpSpPr/>'
        '<p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/>'
        '<a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
        '<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
        '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>'
        '</p:sldLayout>').encode()
    package["ppt/slideLayouts/_rels/slideLayout1.xml.rels"] = _relationships([
        (1, typ + "/slideMaster", "../slideMasters/slideMaster1.xml"),
    ])
    light = story["theme"]["light"]
    package["ppt/theme/theme1.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<a:theme xmlns:a="' + A + '" name="INTEL Theme"><a:themeElements>'
        '<a:clrScheme name="INTEL">'
        '<a:dk1><a:srgbClr val="' + light["text"][1:] + '"/></a:dk1>'
        '<a:lt1><a:srgbClr val="' + light["background"][1:] + '"/></a:lt1>'
        '<a:dk2><a:srgbClr val="334155"/></a:dk2>'
        '<a:lt2><a:srgbClr val="F1F5F9"/></a:lt2>' +
        ''.join('<a:accent' + str(i) + '><a:srgbClr val="' + color +
                '"/></a:accent' + str(i) + '>' for i, color in enumerate(
                (light["accent"][1:], "237753", "9148C8", "006FC9", "B91C1C", "64748B"), start=1)) +
        '<a:hlink><a:srgbClr val="006FC9"/></a:hlink>'
        '<a:folHlink><a:srgbClr val="9148C8"/></a:folHlink>'
        '</a:clrScheme>'
        '<a:fontScheme name="INTEL"><a:majorFont><a:latin typeface="Aptos Display"/>'
        '</a:majorFont><a:minorFont><a:latin typeface="Aptos"/>'
        '</a:minorFont></a:fontScheme>'
        '<a:fmtScheme name="INTEL"><a:fillStyleLst><a:solidFill>'
        '<a:schemeClr val="accent1"/></a:solidFill></a:fillStyleLst>'
        '<a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="accent1"/>'
        '</a:solidFill></a:ln></a:lnStyleLst>'
        '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
        '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="lt1"/>'
        '</a:solidFill></a:bgFillStyleLst>'
        '</a:fmtScheme></a:themeElements></a:theme>').encode()
    package["docProps/core.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"'
        ' xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>INTEL Slides</dc:title>'
        '<dc:creator>INTEL local template</dc:creator></cp:coreProperties>').encode()
    package["docProps/app.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
        '<Application>INTEL</Application><Slides>' + str(len(slides)) +
        '</Slides></Properties>').encode()
    for i, slide in enumerate(slides, start=1):
        package["ppt/slides/slide"+str(i)+".xml"] = _slide_xml(slide, i, light)
        package["ppt/slides/_rels/slide"+str(i)+".xml.rels"] = _relationships([
            (1, typ + "/slideLayout", "../slideLayouts/slideLayout1.xml")])
    return package


def render_pptx(story):
    parts = _package(story)
    sink = io.BytesIO()
    with ZipFile(sink, "w", compression=ZIP_DEFLATED, compresslevel=6) as target:
        for name in sorted(parts):
            target.writestr(name, parts[name])
    data = sink.getvalue()
    verify_pptx(data, story)
    return data


def verify_pptx(data, story):
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_BYTES:
        raise IntelError("INVALID_PPTX", "Invalid PPTX byte budget")
    try:
        with ZipFile(io.BytesIO(data)) as archive:
            names = archive.namelist()
            expected = set(EXPECTED_STATIC)
            for i in range(1, len(story["slides"])+1):
                expected.add(f"ppt/slides/slide{i}.xml")
                expected.add(f"ppt/slides/_rels/slide{i}.xml.rels")
            if set(names) != expected or len(names) != len(expected):
                raise IntelError("INVALID_PPTX", "Unexpected PPTX parts")
            if archive.testzip() is not None:
                raise IntelError("INVALID_PPTX", "PPTX CRC failed")
            for name in names:
                if archive.getinfo(name).file_size > MAX_BYTES:
                    raise IntelError("INVALID_PPTX", "Oversized XML part")
                content = archive.read(name)
                if b"<!DOCTYPE" in content or b"<!ENTITY" in content:
                    raise IntelError("INVALID_PPTX", "Unsafe XML declaration")
                root = ET.fromstring(content)
                if name.endswith(".rels"):
                    for rel in root:
                        if rel.attrib.get("TargetMode") == "External" or "://" in rel.attrib.get("Target", ""):
                            raise IntelError("INVALID_PPTX", "External relationship forbidden")
            presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
            ids = presentation.find(f"{{{P}}}sldIdLst")
            if ids is None or len(ids) != len(story["slides"]):
                raise IntelError("INVALID_PPTX", "Slide count mismatch")
            for i, item in enumerate(story["slides"], start=1):
                root = ET.fromstring(archive.read(f"ppt/slides/slide{i}.xml"))
                found = [node.text or "" for node in root.iter(f"{{{A}}}t")]
                expected_text = [item["title"], *[
                    ("• " if item["layout"] == "bullets" else "") + entry
                    for entry in item["body"]], str(i)]
                if found != expected_text:
                    raise IntelError("INVALID_PPTX", "Slide text mismatch")
    except (BadZipFile, ET.ParseError, KeyError, OSError, ValueError) as exc:
        raise IntelError("INVALID_PPTX", "PPTX structure verification failed") from exc
    return {"pptx_verified": True, "slide_count": len(story["slides"]),
            "sha256": hashlib.sha256(data).hexdigest(),
            "verification_scope": "OOXML parts, CRC, XML, text, relationships"}


def export_slides(content: bytes | str, root: Path, filename: str, fmt: str):
    if not isinstance(filename, str) or not FILENAME.fullmatch(filename) or not filename.endswith("."+fmt):
        raise IntelError("INVALID_PATH", "Use a plain matching .pptx or .json filename")
    if not isinstance(root, Path) or not root.is_dir() or root.is_symlink():
        raise IntelError("INVALID_PATH", "Export root must exist and not be a symlink")
    data = content.encode("utf-8") if isinstance(content, str) else content
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    destination = root.resolve(strict=True) / filename
    try:
        with os.fdopen(os.open(destination, flags, 0o600), "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        if destination.read_bytes() != data:
            raise IntelError("EXPORT_UNVERIFIED", "PPTX export readback mismatch")
    except FileExistsError:
        raise IntelError("DESTINATION_EXISTS", "Refusing to overwrite presentation") from None
    except OSError:
        raise IntelError("EXPORT_FAILED", "Presentation export failed") from None
    return filename, hashlib.sha256(data).hexdigest()


class SlidesRuntime:
    def __init__(self):
        self.capability = slide_capability()

    def execute(self, raw, *, request=None, authorization=None, export_root=None,
                filename=None, mode="template", provider=None):
        manifest = None
        try:
            command = parse_command(raw)
            if command.name != "GENERATE" or command.generator != "SLIDES":
                raise IntelError("INVALID_COMMAND", "Expected /INTEL GENERATE SLIDES")
            objective, audience, preset, accent, fmt, slides = request_slides(command.argument, request)
            (authorization or Authorization()).require(frozenset({Permission.CREATE}))
            if mode != "template" or provider not in (None, "template"):
                raise IntelError("CAPABILITY_UNAVAILABLE", "SLIDES supports only local templates")
            if (export_root is None) != (filename is None):
                raise IntelError("INVALID_REQUEST", "Export requires root and filename")
            manifest = ArtifactManifest(uuid4().hex,
                "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                if fmt == "pptx" else "application/json", "1.0", (), "slides")
            manifest.created_at = datetime.now(timezone.utc).isoformat()
            manifest.provenance = {"producer": "local-deterministic-ooxml",
                                   "model_provider": "not-used", "source_status": "unverified",
                                   "renderer_version": self.capability.version}
            manifest.transition(ArtifactState.READY)
            manifest.transition(ArtifactState.GENERATING)
            story = story_data(objective, audience, preset, accent, slides)
            content = (render_pptx(story) if fmt == "pptx"
                       else json.dumps(story, indent=2, ensure_ascii=True, sort_keys=True)+"\n")
            manifest.transition(ArtifactState.VALIDATING)
            evidence = (verify_pptx(content, story) if fmt == "pptx"
                        else {"storyboard_verified": json.loads(content) == story,
                              "slide_count": len(story["slides"])})
            manifest.validations = {"structure": True, "bounded": len(
                content if isinstance(content, bytes) else content.encode()) <= MAX_BYTES}
            if not all(manifest.validations.values()):
                raise IntelError("VALIDATION_FAILED", "Slides failed validation")
            manifest.transition(ArtifactState.REVIEWED)
            evidence.update({"browser_test": "not_run", "powerpoint_open_test": "not_run",
                             "visual_review": "not_run", "source_verification": "not_run",
                             "layout_overflow_check": "not_run"})
            if export_root is not None:
                path, digest = export_slides(content, export_root, filename, fmt)
                manifest.record_verified_output(path, export_root)
                manifest.transition(ArtifactState.EXPORTED, output_verified=True)
                evidence["file_sha256"] = digest
            return {"ok": True, "capability": "slides", "content": content,
                    "manifest": manifest, "evidence": evidence, "verified": False}
        except IntelError as error:
            if manifest is not None and manifest.state not in (ArtifactState.FAILED, ArtifactState.EXPORTED):
                manifest.transition(ArtifactState.FAILED)
            return {**error.as_result(), "manifest": manifest}
