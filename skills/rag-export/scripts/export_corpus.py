#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""export_corpus.py — 위키(20-nodes/30-topics) → RAG 코퍼스 내보내기

이 저장소의 second brain / curriculum-kb 위키를 외부 RAG 도구가 먹을 수 있는
세 가지 범용 포맷으로 변환한다 (표준 라이브러리만 사용):

  rag-export/corpus.jsonl   한 줄 = 노드 1개 (id·type·summary·tags·edges 메타 포함)
                            → LlamaIndex / LangChain / LightRAG / 커스텀 파이프라인용
  rag-export/corpus.md      전체 노드를 구분자로 병합한 단일 마크다운
                            → AnythingLLM / Open WebUI / ChatGPT 프로젝트 업로드용
  rag-export/graph.json     노드 + 타입 엣지 그래프 (nodes[], edges[])
                            → GraphRAG류 / Neo4j / 시각화 도구용

사용법:
    python export_corpus.py [위키루트] [-o 출력폴더]
    (인자 없으면 현재 폴더를 위키 루트로 간주)

원천(10-sources/)과 위키 본문은 절대 수정하지 않는다 — 출력은 전부 생성물.
"""
import argparse
import json
import re
import sys
from pathlib import Path

EDGE_RE = re.compile(r"^\s*-\s*([A-Za-z_]+)::\s*\[\[([^\]]+)\]\]", re.M)
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def parse_frontmatter(text):
    """단순 YAML frontmatter 파서 (key: value / key: [a, b] / 따옴표만 지원)."""
    meta, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            raw, body = text[3:end], text[end + 4:]
            for line in raw.splitlines():
                if ":" not in line or line.strip().startswith("#"):
                    continue
                key, _, val = line.partition(":")
                key, val = key.strip(), val.strip()
                if not key or " " in key:
                    continue
                if val.startswith("[") and val.endswith("]"):
                    items = [v.strip().strip("'\"") for v in val[1:-1].split(",")]
                    meta[key] = [v for v in items if v]
                else:
                    meta[key] = val.strip("'\"")
    return meta, body.strip()


def collect_nodes(root: Path):
    nodes = []
    for folder in ("20-nodes", "30-topics"):
        d = root / folder
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*.md")):
            if f.name.upper().startswith("README"):
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_frontmatter(text)
            edges = [{"type": t, "target": _clean_target(g)}
                     for t, g in EDGE_RE.findall(body)]
            nodes.append({
                "id": meta.get("id") or f.stem,
                "path": f.relative_to(root).as_posix(),
                "type": meta.get("type", ""),
                "title": meta.get("title", f.stem),
                "summary": meta.get("summary", ""),
                "tags": meta.get("tags", []) if isinstance(meta.get("tags"), list) else [meta.get("tags")] if meta.get("tags") else [],
                "status": meta.get("status", ""),
                "source": meta.get("source", ""),
                "updated": meta.get("updated", ""),
                "edges": edges,
                "text": body,
            })
    return nodes


def _clean_target(target: str) -> str:
    return target.split("|")[0].split("/")[-1].strip()


def main(argv=None):
    ap = argparse.ArgumentParser(description="위키 → RAG 코퍼스(jsonl/md/graph) 내보내기")
    ap.add_argument("root", nargs="?", default=".", help="위키 루트 (기본: 현재 폴더)")
    ap.add_argument("-o", "--output", default=None, help="출력 폴더 (기본: <루트>/rag-export)")
    ap.add_argument("--split-by", choices=["type", "status"], default=None,
                    help="corpus-<값>.md로 분리 내보내기 — 목적이 다른 노드를 같은 벡터 공간에 섞지 않기 위함")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    if not (root / "20-nodes").is_dir() and not (root / "30-topics").is_dir():
        print(f"FAIL: {root} 에 20-nodes/ 또는 30-topics/ 가 없음 — 위키 루트가 맞는지 확인", file=sys.stderr)
        return 1

    nodes = collect_nodes(root)
    if not nodes:
        print("FAIL: 노드가 없음 (20-nodes/가 비어 있음)", file=sys.stderr)
        return 1

    out = Path(args.output) if args.output else root / "rag-export"
    out.mkdir(parents=True, exist_ok=True)

    # 1) corpus.jsonl — 벡터 인덱싱용 (메타데이터 동봉)
    with (out / "corpus.jsonl").open("w", encoding="utf-8") as f:
        for n in nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")

    # 2) corpus.md — 업로드형 도구용 병합본.
    #    임베딩 모델 다수가 title/body 구조로 학습돼 있어 노드 경계를 "## 제목 + 요약 + 본문"
    #    헤더 구조로 보존한다(제목 없는 연속 텍스트보다 검색 성능이 좋다).
    def write_corpus_md(path: Path, subset, label: str):
        with path.open("w", encoding="utf-8") as f:
            f.write(f"# 위키 코퍼스{label} (자동 생성 — 원본: 20-nodes/, 30-topics/)\n")
            for n in subset:
                f.write(f"\n\n---\n\n## {n['title']}  \n")
                f.write(f"(type: {n['type'] or '?'} · id: {n['id']} · status: {n['status'] or '?'})  \n")
                if n["summary"]:
                    f.write(f"**요약**: {n['summary']}\n\n")
                f.write(n["text"])

    write_corpus_md(out / "corpus.md", nodes, "")
    split_files = []
    if args.split_by:
        groups = {}
        for n in nodes:
            groups.setdefault(n.get(args.split_by) or "unknown", []).append(n)
        for val, subset in sorted(groups.items()):
            safe = re.sub(r"[^0-9A-Za-z가-힣_-]", "_", val)
            p = out / f"corpus-{safe}.md"
            write_corpus_md(p, subset, f" — {args.split_by}={val}")
            split_files.append(f"{p.name}({len(subset)})")

    # 3) graph.json — 타입 엣지 그래프
    # resolved: "node"(노드 참조) | "source"(10-sources 원천 참조 — 유효) | False(깨진 링크)
    ids = {n["id"] for n in nodes}
    # 위키링크는 파일명(stem) 기준으로 해석된다(Obsidian 규칙) — id가 경로형(30-topics/X)이어도 매칭
    stem_to_id = {Path(n["path"]).stem: n["id"] for n in nodes}
    title_to_id = {n["title"]: n["id"] for n in nodes}
    source_stems = set()
    src_dir = root / "10-sources"
    if src_dir.is_dir():
        source_stems = {f.stem for f in src_dir.rglob("*") if f.is_file()}
    edges = []
    for n in nodes:
        for e in n["edges"]:
            t = e["target"]
            dst = t if t in ids else stem_to_id.get(t) or title_to_id.get(t) or t
            if dst in ids:
                resolved = "node"
            elif dst in source_stems:
                resolved = "source"
            else:
                resolved = False
            edges.append({"src": n["id"], "edge": e["type"], "dst": dst, "resolved": resolved})
    graph = {
        "nodes": [{k: n[k] for k in ("id", "type", "title", "summary", "tags", "status")} for n in nodes],
        "edges": edges,
    }
    (out / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=1), encoding="utf-8")

    unresolved = sum(1 for e in edges if not e["resolved"])
    src_refs = sum(1 for e in edges if e["resolved"] == "source")
    print(f"OK  노드 {len(nodes)}개, 엣지 {len(edges)}개(원천 참조 {src_refs}, 깨진 링크 {unresolved}) → {out}")
    print(f"    corpus.jsonl / corpus.md / graph.json")
    if split_files:
        print(f"    분리: {', '.join(split_files)}")
    if unresolved:
        print(f"    참고: 깨진 링크 {unresolved}개는 대상 노드/원천이 없는 것 — /lint 로 점검 가능")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
