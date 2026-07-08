#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ingest_youtube.py — 유튜브 영상 → 타임스탬프 딥링크 달린 마크다운 전사본

전략 (검증된 파이프라인의 파이썬 이식):
  1) yt-dlp로 자막(.vtt)만 다운로드 — 정식 자막(--write-subs)과 자동 생성
     자막(--write-auto-subs)을 둘 다 시도. 영상 다운로드는 건너뜀. API 키 불필요.
  2) VTT를 라이브러리 없이 직접 파싱 — 인라인 태그(<c>, <00:00:01.000>)·HTML 엔티티
     정리, 자동자막 특유의 "롤링 중복"(직전 cue 꼬리 = 다음 cue 머리)을
     suffix/prefix 매칭으로 제거. startSec을 보존해 youtu.be/<id>?t=<초> 딥링크 생성.
  3) 자막이 아예 없으면 (옵션) Whisper STT 폴백 — yt-dlp로 오디오만 추출 후
     OpenAI Whisper API(verbose_json, 세그먼트 타임스탬프 유지). OPENAI_API_KEY 필요.

사용법:
    python ingest_youtube.py <유튜브URL> [-o 출력.md] [--lang ko]
환경변수:
    TRANSCRIPT_METHOD  captions-then-whisper(기본) | captions-only
    TRANSCRIPT_LANG    자막 언어 (기본 ko)
    STT_MODEL          Whisper 모델 (기본 whisper-1)
의존성: yt-dlp (pip install yt-dlp). Whisper 폴백 시에만 openai + OPENAI_API_KEY.
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TAG_RE = re.compile(r"<[^>]+>")          # <c>, <00:00:01.000>, </c> 등 인라인 태그
TS_RE = re.compile(
    r"(?:(\d+):)?(\d{1,2}):(\d{2})\.(\d{3})\s*-->\s*(?:(\d+):)?(\d{1,2}):(\d{2})\.(\d{3})")


def run_ytdlp(args, timeout=300):
    exe = shutil.which("yt-dlp")
    if not exe:
        raise RuntimeError("yt-dlp가 없습니다:  pip install yt-dlp")
    r = subprocess.run([exe, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp 실패: {(r.stderr or '').strip().splitlines()[-1] if r.stderr else '원인 불명'}")
    return r.stdout


def video_meta(url):
    out = run_ytdlp(["--dump-json", "--skip-download", "--no-playlist", url])
    m = json.loads(out.splitlines()[0])
    return {"id": m.get("id"), "title": m.get("title", ""), "channel": m.get("channel") or m.get("uploader", ""),
            "upload_date": m.get("upload_date", ""), "duration": m.get("duration") or 0}


def download_vtt(url, lang, tmpdir):
    """정식 자막 + 자동 자막을 시도해 .vtt 경로를 반환 (없으면 None)."""
    run_ytdlp(["--write-subs", "--write-auto-subs", "--sub-langs", f"{lang},{lang}-*",
               "--skip-download", "--sub-format", "vtt", "--no-playlist",
               "-o", str(Path(tmpdir) / "%(id)s.%(ext)s"), url])
    vtts = sorted(Path(tmpdir).glob("*.vtt"),
                  key=lambda p: (0 if f".{lang}." in p.name else 1, len(p.name)))
    return vtts[0] if vtts else None


def parse_ts(m, base):
    h = int(m.group(base) or 0)
    return h * 3600 + int(m.group(base + 1)) * 60 + int(m.group(base + 2)) + int(m.group(base + 3)) / 1000


def parse_vtt(path: Path):
    """VTT → [{start, end, text}] — 태그/엔티티 정리 + 롤링 중복 제거."""
    segs = []
    cur = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        m = TS_RE.search(line)
        if m:
            if cur and cur["text"]:
                segs.append(cur)
            cur = {"start": parse_ts(m, 1), "end": parse_ts(m, 5), "text": ""}
        elif cur is not None and line and line != "WEBVTT" and not line.startswith(("NOTE", "Kind:", "Language:", "STYLE")):
            text = html.unescape(TAG_RE.sub("", line)).strip()
            if text:
                cur["text"] = (cur["text"] + " " + text).strip()
    if cur and cur["text"]:
        segs.append(cur)

    # 롤링 중복 제거: 직전 텍스트의 꼬리가 이번 텍스트의 머리에 반복되는 자동자막 패턴
    cleaned = []
    for s in segs:
        if cleaned:
            prev = cleaned[-1]["text"]
            t = s["text"]
            if t == prev:
                cleaned[-1]["end"] = s["end"]
                continue
            overlap = min(len(prev), len(t))
            while overlap > 0 and not prev.endswith(t[:overlap]):
                overlap -= 1
            t = t[overlap:].strip()
            if not t:
                cleaned[-1]["end"] = s["end"]
                continue
            s = {**s, "text": t}
        cleaned.append(s)
    return cleaned


def whisper_fallback(url, tmpdir, lang):
    """자막 없음 → 오디오 추출 후 OpenAI Whisper STT (세그먼트 타임스탬프 유지)."""
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("자막 없음. Whisper 폴백에는 OPENAI_API_KEY가 필요합니다 "
                           "(과금 발생 — 원치 않으면 TRANSCRIPT_METHOD=captions-only)")
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("Whisper 폴백에는 openai 패키지가 필요합니다:  pip install openai")
    run_ytdlp(["-x", "--audio-format", "mp3", "--no-playlist",
               "-o", str(Path(tmpdir) / "%(id)s.%(ext)s"), url], timeout=1800)
    mp3s = list(Path(tmpdir).glob("*.mp3"))
    if not mp3s:
        raise RuntimeError("오디오 추출 실패")
    audio = mp3s[0]
    if audio.stat().st_size > 25 * 1024 * 1024:
        raise RuntimeError("오디오가 25MB를 초과 — Whisper API 한도. 긴 영상은 분할 필요")
    client = OpenAI()
    with audio.open("rb") as f:
        tr = client.audio.transcriptions.create(
            model=os.environ.get("STT_MODEL", "whisper-1"),
            file=f, language=lang, response_format="verbose_json")
    return [{"start": s.start, "end": s.end, "text": s.text.strip()}
            for s in (tr.segments or []) if s.text.strip()]


def fmt_ts(sec):
    sec = int(sec)
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60}:{sec % 60:02d}"


def to_markdown(meta, segs, para_gap=45):
    """세그먼트를 ~para_gap초 단위 문단으로 묶고 문단마다 딥링크를 단다."""
    vid = meta["id"]
    lines = [f"# {meta['title']} (유튜브 전사본)", "",
             f"> 원본: https://youtu.be/{vid} · 채널: {meta['channel']} · "
             f"업로드: {meta['upload_date']} · 길이: {fmt_ts(meta['duration'])}",
             "> 이 파일은 생성물(ingest_youtube.py) — 원본 영상이 진실의 원천", ""]
    para, para_start = [], None
    for s in segs:
        if para_start is None:
            para_start = s["start"]
        para.append(s["text"])
        if s["end"] - para_start >= para_gap:
            lines.append(f"[{fmt_ts(para_start)}](https://youtu.be/{vid}?t={int(para_start)}) {' '.join(para)}")
            lines.append("")
            para, para_start = [], None
    if para:
        lines.append(f"[{fmt_ts(para_start)}](https://youtu.be/{vid}?t={int(para_start)}) {' '.join(para)}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="유튜브 → 타임스탬프 마크다운 전사본")
    ap.add_argument("url", help="유튜브 영상 URL")
    ap.add_argument("-o", "--output", help="출력 md 경로 (기본: youtube-<id>.extracted.md)")
    ap.add_argument("--lang", default=os.environ.get("TRANSCRIPT_LANG", "ko"), help="자막 언어 (기본 ko)")
    args = ap.parse_args(argv)
    method = os.environ.get("TRANSCRIPT_METHOD", "captions-then-whisper")

    meta = video_meta(args.url)
    tmpdir = tempfile.mkdtemp(prefix="yt-ingest-")
    try:
        vtt = download_vtt(args.url, args.lang, tmpdir)
        if vtt:
            segs, how = parse_vtt(vtt), f"자막({vtt.name.split('.')[-2]})"
        elif method == "captions-then-whisper":
            segs, how = whisper_fallback(args.url, tmpdir, args.lang), "Whisper STT"
        else:
            raise RuntimeError(f"'{args.lang}' 자막 없음 (captions-only 모드)")
        if not segs:
            raise RuntimeError("전사 결과가 비어 있음")
        out = Path(args.output) if args.output else Path(f"youtube-{meta['id']}.extracted.md")
        out.write_text(to_markdown(meta, segs), encoding="utf-8")
        print(f"OK  {meta['title']} → {out} ({how}, 세그먼트 {len(segs)}개)")
        return 0
    except Exception as e:
        print(f"FAIL {args.url}: {e}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
