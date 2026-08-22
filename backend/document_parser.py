# -*- coding: utf-8 -*-
"""Local text extraction for contract TXT/Markdown/DOCX/PDF files."""

from __future__ import annotations

import base64
import io
import re
import zipfile
from pathlib import Path


MAX_FILE_BYTES = 15 * 1024 * 1024


def extract_document_text(filename: str, content_base64: str) -> dict[str, str | int]:
    try:
        content = base64.b64decode(content_base64, validate=True)
    except Exception as exc:
        raise ValueError("文件内容不是有效的Base64数据") from exc
    if not content:
        raise ValueError("文件不能为空")
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("文件不能超过15MB")
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md"}:
        text = content.decode("utf-8-sig", errors="replace")
    elif suffix == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                xml = archive.read("word/document.xml").decode("utf-8")
            text = re.sub(r"</w:p>", "\n", xml)
            text = re.sub(r"<[^>]+>", "", text)
            text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        except (zipfile.BadZipFile, KeyError) as exc:
            raise ValueError("DOCX文件损坏或格式不受支持") from exc
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ValueError("PDF解析依赖未安装，请重新安装Order Studio插件") from exc
        try:
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise ValueError("PDF文件损坏、加密或无法读取") from exc
        if not text.strip():
            raise ValueError("PDF未提取到文字，扫描件请先通过OCR转换")
    else:
        raise ValueError("仅支持TXT、Markdown、DOCX和文本型PDF")
    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        raise ValueError("文件中没有可审查的文本")
    return {"filename": filename, "extension": suffix, "text": text, "characters": len(text)}
