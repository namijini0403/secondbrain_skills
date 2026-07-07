#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract.py — HWP/HWPX/PDF/XLSX/DOCX 텍스트 추출기 (second brain / RAG ingest용)

사용법:
    python extract.py <파일> [<파일2> ...] [-o 출력.md] [--stdout]

- 기본: 각 입력 옆에 <이름>.extracted.md 생성 (-o 는 입력 1개일 때만)
- HWPX/XLSX/DOCX: 표준 라이브러리만 사용 (설치 불필요)
- HWP(v5):  pip install olefile
- PDF:      pip install pypdf
- 암호 걸린 문서, HWP 배포용(DRM) 문서는 지원하지 않음 (명확한 오류로 안내)
"""
import argparse
import io
import re
import struct
import sys
import zipfile
import zlib
from pathlib import Path

try:  # 신뢰할 수 없는 문서의 XML 파싱 — XXE/billion-laughs 방어 (있으면 사용)
    import defusedxml.ElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET


def _iter_local(root, name):
    """네임스페이스를 무시하고 로컬 태그명으로 순회 (Element.iter는 {*} 미지원)."""
    for el in root.iter():
        if isinstance(el.tag, str) and el.tag.rsplit("}", 1)[-1] == name:
            yield el


def _find_local(elem, name):
    for el in _iter_local(elem, name):
        return el
    return None


# ---------------------------------------------------------------- HWPX
def extract_hwpx(path: Path) -> str:
    """HWPX = OWPML(XML) zip. Contents/section*.xml의 <hp:t> 텍스트를 문단 단위로 모은다."""
    out = []
    with zipfile.ZipFile(path) as z:
        sections = sorted(n for n in z.namelist()
                          if re.match(r"Contents/section\d+\.xml$", n))
        if not sections:
            raise ValueError("Contents/section*.xml 없음 — HWPX 파일이 맞는지 확인")
        for name in sections:
            root = ET.fromstring(z.read(name))
            for p in _iter_local(root, "p"):
                line = "".join(t.text or "" for t in _iter_local(p, "t")).strip()
                if line:
                    out.append(line)
    return "\n\n".join(out)


# ---------------------------------------------------------------- HWP (v5 binary)
# 참고: HWP 5.0 파일 형식 공개 문서(한글과컴퓨터). BodyText/Section* 스트림의
# 레코드 중 HWPTAG_PARA_TEXT(=0x10+51=67)만 UTF-16LE로 디코드한다.
_HWP_SINGLE_CTRL = {0, 10, 13, 24, 25, 26, 27, 28, 29, 30, 31}  # 1 WCHAR 컨트롤


def extract_hwp(path: Path) -> str:
    try:
        import olefile
    except ImportError:
        raise RuntimeError("HWP 추출에는 olefile이 필요합니다:  pip install olefile")

    if not olefile.isOleFile(str(path)):
        raise ValueError("OLE 컨테이너가 아님 — HWP 5.x 파일이 맞는지 확인 (HWP 3.x 미지원)")

    ole = olefile.OleFileIO(str(path))
    try:
        header = ole.openstream("FileHeader").read()
        if not header.startswith(b"HWP Document File"):
            raise ValueError("FileHeader 시그니처 불일치 — HWP 파일이 아님")
        flags = struct.unpack_from("<I", header, 36)[0]
        compressed = bool(flags & 0x01)
        if flags & 0x02:
            raise ValueError("암호가 설정된 HWP — 암호 해제 후 다시 시도")
        if ole.exists("ViewText/Section0"):
            raise ValueError("배포용(DRM) HWP — 한글에서 '다른 이름으로 저장' 후 다시 시도")

        sections = sorted(
            (e for e in ole.listdir() if e[0] == "BodyText"),
            key=lambda e: int(re.sub(r"\D", "", e[1]) or 0),
        )
        if not sections:
            raise ValueError("BodyText 스트림 없음")

        paras = []
        for entry in sections:
            data = ole.openstream(entry).read()
            if compressed:
                data = zlib.decompress(data, -15)
            paras.extend(_hwp_para_texts(data))
        return "\n\n".join(p for p in (s.strip() for s in paras) if p)
    finally:
        ole.close()


def _hwp_para_texts(data: bytes):
    """섹션 바이트에서 레코드를 걸으며 PARA_TEXT(67) 레코드만 텍스트로 디코드."""
    pos, n = 0, len(data)
    while pos + 4 <= n:
        (hdr,) = struct.unpack_from("<I", data, pos)
        tag = hdr & 0x3FF
        size = (hdr >> 20) & 0xFFF
        pos += 4
        if size == 0xFFF:  # 확장 크기
            (size,) = struct.unpack_from("<I", data, pos)
            pos += 4
        if tag == 67:  # HWPTAG_PARA_TEXT
            yield _hwp_decode_text(data[pos:pos + size])
        pos += size


def _hwp_decode_text(chunk: bytes) -> str:
    out = []
    i, n = 0, len(chunk) - 1
    while i < n:
        (c,) = struct.unpack_from("<H", chunk, i)
        if c < 32:
            if c in _HWP_SINGLE_CTRL:
                if c in (10, 13):
                    out.append("\n")
                i += 2
            else:  # 인라인/확장 컨트롤 = 8 WCHAR(16바이트) 점유
                i += 16
        else:
            out.append(chr(c))
            i += 2
    return "".join(out)


# ---------------------------------------------------------------- PDF
def extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # 구버전 폴백
        except ImportError:
            raise RuntimeError("PDF 추출에는 pypdf가 필요합니다:  pip install pypdf")
    reader = PdfReader(str(path))
    if getattr(reader, "is_encrypted", False):
        try:
            reader.decrypt("")
        except Exception:
            raise ValueError("암호가 설정된 PDF — 암호 해제 후 다시 시도")
    pages = []
    for idx, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").strip()
        pages.append(f"<!-- p.{idx} -->\n{text}" if text else f"<!-- p.{idx}: (텍스트 없음/이미지) -->")
    body = "\n\n".join(pages)
    if not re.search(r"[가-힣A-Za-z0-9]", body):
        body += "\n\n> ⚠️ 텍스트 레이어가 없는 스캔 PDF일 수 있습니다. OCR이 필요합니다."
    return body


# ---------------------------------------------------------------- XLSX
def extract_xlsx(path: Path, max_rows: int = 5000) -> str:
    """XLSX zip을 직접 파싱해 시트별 마크다운 표로. (openpyxl 불필요)"""
    with zipfile.ZipFile(path) as z:
        # 공유 문자열
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in _iter_local(root, "si"):
                shared.append("".join(t.text or "" for t in _iter_local(si, "t")))
        # 시트 이름 ↔ 파일 매핑 (workbook.xml + rels)
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rel_map = {r.get("Id"): r.get("Target") for r in _iter_local(rels, "Relationship")}
        sheets = []
        for s in _iter_local(wb, "sheet"):
            rid = s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            target = (rel_map.get(rid) or "").lstrip("/")
            if target and not target.startswith("xl/"):
                target = "xl/" + target
            sheets.append((s.get("name"), target))

        out = []
        for name, target in sheets:
            if not target or target not in z.namelist():
                continue
            root = ET.fromstring(z.read(target))
            rows = []
            for row in _iter_local(root, "row"):
                cells = {}
                for c in _iter_local(row, "c"):
                    ref = c.get("r", "")
                    col = _col_index(re.sub(r"\d", "", ref)) if ref else len(cells)
                    t = c.get("t")
                    if t == "s":
                        v = _find_local(c, "v")
                        val = shared[int(v.text)] if v is not None and v.text else ""
                    elif t == "inlineStr":
                        val = "".join(x.text or "" for x in _iter_local(c, "t"))
                    else:
                        v = _find_local(c, "v")
                        val = v.text if v is not None and v.text else ""
                    cells[col] = (val or "").strip()
                if any(cells.values()):
                    width = max(cells) + 1 if cells else 0
                    rows.append([cells.get(i, "") for i in range(width)])
                if len(rows) >= max_rows:
                    rows.append([f"… (이후 행 생략: {max_rows}행 초과)"])
                    break
            if rows:
                width = max(len(r) for r in rows)
                md = [f"## 시트: {name}", ""]
                for i, r in enumerate(rows):
                    r = [cell.replace("|", "\\|").replace("\n", " ") for cell in r] + [""] * (width - len(r))
                    md.append("| " + " | ".join(r) + " |")
                    if i == 0:
                        md.append("|" + "---|" * width)
                out.append("\n".join(md))
        return "\n\n".join(out) if out else "(빈 통합문서)"


def _col_index(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch.upper()) - 64)
    return max(n - 1, 0)


# ---------------------------------------------------------------- DOCX
def extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    out = []
    for p in _iter_local(root, "p"):
        line = "".join(t.text or "" for t in _iter_local(p, "t")).strip()
        if line:
            out.append(line)
    return "\n\n".join(out)


# ---------------------------------------------------------------- main
HANDLERS = {
    ".hwpx": extract_hwpx,
    ".hwp": extract_hwp,
    ".pdf": extract_pdf,
    ".xlsx": extract_xlsx,
    ".docx": extract_docx,
}


def main(argv=None):
    ap = argparse.ArgumentParser(description="HWP/HWPX/PDF/XLSX/DOCX → 마크다운 텍스트 추출")
    ap.add_argument("files", nargs="+", help="추출할 파일(들)")
    ap.add_argument("-o", "--output", help="출력 경로 (입력 1개일 때만)")
    ap.add_argument("--stdout", action="store_true", help="파일 대신 표준출력으로")
    args = ap.parse_args(argv)

    if args.output and len(args.files) > 1:
        ap.error("-o 는 입력이 1개일 때만 쓸 수 있습니다")

    failed = 0
    for f in args.files:
        path = Path(f)
        ext = path.suffix.lower()
        try:
            if not path.exists():
                raise FileNotFoundError(f"파일 없음: {path}")
            handler = HANDLERS.get(ext)
            if handler is None:
                raise ValueError(f"지원하지 않는 확장자: {ext} (지원: {', '.join(HANDLERS)})")
            text = handler(path)
            header = f"# {path.name} (추출본)\n\n> 원본: `{path.name}` · 추출: extract.py · 이 파일은 생성물 — 원본이 진실의 원천\n\n"
            content = header + text.strip() + "\n"
            if args.stdout:
                sys.stdout.write(content)
            else:
                out = Path(args.output) if args.output else path.with_suffix(path.suffix + ".extracted.md")
                out.write_text(content, encoding="utf-8")
                chars = len(text)
                print(f"OK  {path.name} → {out.name} ({chars:,}자)")
        except Exception as e:
            failed += 1
            print(f"FAIL {path.name}: {e}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
