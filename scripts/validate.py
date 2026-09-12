#!/usr/bin/env python3
"""novel2agent-jp: TOML 設定の機械検証 (P1)

スキーマ: schema/toml-schema.md
方針: 値を推測で埋めない。構造エラーは exit 1、警告系は明示出力して継続。

Usage:
  python validate.py --project-dir <path>
  python validate.py --project-dir <path> --index    # ID 一覧のみ出力
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

ID_PREFIXES = {"chara", "plot", "fs", "world"}
VALID_WORK_STATUS = {"planning", "writing", "revision", "complete"}
VALID_CHAPTER_STATUS = {"draft", "written", "revised", "confirmed"}
VALID_SUMMARY_STATUS = {"proposed", "confirmed"}
VALID_CONSTRAINT_KINDS = {"forbidden_words", "unknown_to", "era"}

ERR = "[ERROR]"
WARN = "[WARN]"


# ---------------------------------------------------------------- ローダ

def load_all(project: Path) -> tuple[dict[Path, dict], list[tuple[Path, str]]]:
    files: dict[Path, dict] = {}
    parse_errors: list[tuple[Path, str]] = []
    paths: list[Path] = []
    for sub in ("character", "worldbuilding", "plot"):
        d = project / sub
        if d.is_dir():
            paths.extend(sorted(d.glob("*.toml")))
    meta = project / "meta.toml"
    if meta.is_file():
        paths.append(meta)
    for f in paths:
        try:
            files[f] = tomllib.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            parse_errors.append((f, str(e)))
    return files, parse_errors


def by_prefix(files: dict[Path, dict], prefix: str) -> list[tuple[Path, dict]]:
    return [(f, d) for f, d in sorted(files.items())
            if f.stem.split("-")[0] == prefix or (prefix == "plot" and f.stem.startswith("plot-ch"))]


# ---------------------------------------------------------------- チェック

class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, path, msg):
        self.errors.append(f"{ERR} {path.name}: {msg}")

    def warn(self, path, msg):
        self.warnings.append(f"{WARN} {path.name}: {msg}")


def type_ok(v, typ) -> bool:
    if typ is int:
        return isinstance(v, int) and not isinstance(v, bool)
    return isinstance(v, typ)


def check_keys(data: dict, required: dict[str, type], path, label: str, r: Report) -> None:
    missing = [k for k in required if k not in data]
    if missing:
        r.error(path, f"{label}: 必須キー欠落 {missing}")
    wrong = [
        f"{k}(期待{t.__name__},実{type(data[k]).__name__})"
        for k, t in required.items() if k in data and not type_ok(data[k], t)
    ]
    if wrong:
        r.error(path, f"{label}: 型不正 {wrong}")


def check_id(stem: str, data: dict, path, r: Report) -> None:
    if "id" not in data:
        r.error(path, "id キーが存在しない")
    elif data["id"] != stem:
        r.error(path, f"ファイル名=ID 不一致: id={data['id']!r}")
    pref, sep, num = stem.partition("-")
    if not sep or pref not in ID_PREFIXES:
        r.error(path, f"ID prefix 不正: {stem} (許可 {sorted(ID_PREFIXES)})")
        return
    # plot 章ファイルは plot-chNN 形式を許可（スキーマ §3 の例に準拠）
    if pref == "plot":
        if not (stem.startswith("plot-ch") and stem[7:].isdigit()
                and len(stem[7:]) == 2 and int(stem[7:]) >= 1):
            r.error(path, f"ID 連番不正: {stem} (期待 plot-chNN)")
    elif len(num) != 3 or not num.isdigit() or int(num) < 1:
        r.error(path, f"ID 連番不正: {stem} (期待 {pref}-NNN)")


def ranges_overlap(known: list[tuple[int, int | None]], a: int, b: int | None, path, idx: int, r: Report) -> None:
    """versions 章範囲重複の正確判定"""
    for k, (x, y) in enumerate(known):
        hi_a = 10**9 if b is None else b
        hi_x = 10**9 if y is None else y
        if max(a, x) <= min(hi_a, hi_x):
            r.error(path, f"versions[{idx}]: 章範囲重複 ({a}..{b if b is not None else '∞'} vs {x}..{y if y is not None else '∞'})")
            return


def validate_characters(chars, r: Report) -> set[str]:
    ids: set[str] = set()
    relations: list[tuple[Path, int, str]] = []
    for path, data in chars:
        check_id(path.stem, data, path, r)
        check_keys(
            data,
            {"id": str, "name_ja": str, "name_ruby": str, "role": str},
            path, "character ルート", r,
        )
        if type_ok(data.get("id"), str):
            ids.add(data["id"])
        basic = data.get("basic")
        if basic is None:
            r.error(path, "[basic] セクション必須")
        elif not isinstance(basic, dict):
            r.error(path, "[basic] がテーブルでない")
        else:
            check_keys(basic, {"gender": str, "age": int, "first_person": str}, path, "[basic]", r)
        versions = data.get("versions", [])
        if versions and not isinstance(versions, list):
            r.error(path, "versions は [[versions]] 配列")
            versions = []
        known: list[tuple[int, int | None]] = []
        for i, v in enumerate(versions):
            if not isinstance(v, dict):
                r.error(path, f"versions[{i}] がテーブルでない")
                continue
            a = v.get("from_chapter")
            b = v.get("to_chapter")
            if not type_ok(a, int):
                r.error(path, f"versions[{i}]: from_chapter 必須(int)")
                continue
            if b is not None and (not type_ok(b, int) or b < a):
                r.error(path, f"versions[{i}]: 章範囲逆転 (from={a}, to={b})")
                continue
            ranges_overlap(known, a, b, path, i, r)
            known.append((a, b))
        for i, rel in enumerate(data.get("relations", [])):
            if not isinstance(rel, dict):
                r.error(path, f"relations[{i}] がテーブルでない")
                continue
            t = rel.get("target")
            if not type_ok(t, str):
                r.error(path, f"relations[{i}]: target 必須(str)")
            else:
                relations.append((path, i, t))
    for path, i, t in relations:
        if t not in ids:
            r.error(path, f"relations[{i}]: target '{t}' が存在しない chara ID")
    return ids


def validate_worlds(worlds, ref_ids: set[str], r: Report) -> None:
    for path, data in worlds:
        check_id(path.stem, data, path, r)
        check_keys(
            data,
            {"id": str, "title": str, "kind": str},
            path, "world ルート", r,
        )
        for i, c in enumerate(data.get("constraints", [])):
            if not isinstance(c, dict):
                r.error(path, f"constraints[{i}] がテーブルでない")
                continue
            kind = c.get("kind")
            if not type_ok(kind, str):
                r.error(path, f"constraints[{i}]: kind 必須(str)")
            elif kind not in VALID_CONSTRAINT_KINDS:
                r.error(path, f"constraints[{i}]: kind 不正 '{kind}'")
            elif kind == "forbidden_words" and not (isinstance(c.get("words"), list) and c["words"]):
                r.error(path, f"constraints[{i}]: forbidden_words には words 配列必須")
            elif kind == "unknown_to":
                if not type_ok(c.get("target"), str):
                    r.error(path, f"constraints[{i}]: unknown_to には target(ID) 必須")
                elif c["target"] not in ref_ids:
                    r.error(path, f"constraints[{i}]: target '{c['target']}' が存在しない")


def validate_plots(plots, ref_ids: set[str], r: Report) -> None:
    fs_ids: set[str] = set()
    for path, data in plots:
        check_id(path.stem, data, path, r)
        check_keys(
            data,
            {"id": str, "chapter": int, "title": str},
            path, "plot ルート", r,
        )
        ch = data.get("chapter")
        if type_ok(ch, int) and path.stem != f"plot-ch{ch:02d}":
            r.warn(path, f"chapter={ch} とファイル名 {path.stem} の番号が一致しない")
        if type_ok(data.get("pov"), str) and data["pov"] not in ref_ids:
            r.error(path, f"pov: ID '{data['pov']}' が存在しない")

        scenes = data.get("scenes")
        if not isinstance(scenes, list) or not scenes:
            r.error(path, "scenes 必須・1件以上")
            scenes = []
        for i, s in enumerate(scenes):
            if not isinstance(s, dict):
                r.error(path, f"scenes[{i}] がテーブルでない")
                continue
            check_keys(
                s,
                {"title": str, "location": str, "pov": str, "characters": list, "content": str},
                path, f"scenes[{i}]", r,
            )
            chars_list = s.get("characters")
            if isinstance(chars_list, list):
                for cid in chars_list:
                    if not type_ok(cid, str):
                        r.error(path, f"scenes[{i}].characters: ID が文字列でない: {cid!r}")
                    elif cid not in ref_ids:
                        r.error(path, f"scenes[{i}].characters: ID '{cid}' が存在しない")
            if type_ok(s.get("pov"), str) and s["pov"] not in ref_ids:
                r.error(path, f"scenes[{i}].pov: ID '{s['pov']}' が存在しない")

        for i, f in enumerate(data.get("foreshadowing", [])):
            if not isinstance(f, dict):
                r.error(path, f"foreshadowing[{i}] がテーブルでない")
                continue
            check_keys(f, {"id": str, "content": str, "resolve_chapter": int}, path, f"foreshadowing[{i}]", r)
            fid = f.get("id")
            if type_ok(fid, str):
                if fid in fs_ids:
                    r.error(path, f"foreshadowing id 重複: {fid}")
                fs_ids.add(fid)
                if not fid.startswith("fs-"):
                    r.error(path, f"foreshadowing id prefix 不正: {fid}")
            rc = f.get("resolve_chapter")
            ra = f.get("resolved_at")
            if type_ok(rc, int) and type_ok(ra, int) and ra != rc:
                r.warn(path, f"foreshadowing[{i}]: resolved_at={ra} が resolve_chapter={rc} と不一致")

        for i, e in enumerate(data.get("established", [])):
            if not isinstance(e, dict):
                r.error(path, f"established[{i}] がテーブルでない")
                continue
            st = e.get("status")
            if st is not None and st not in VALID_SUMMARY_STATUS:
                r.error(path, f"established[{i}]: status 不正 '{st}'")
            elif st == "proposed":
                r.warn(path, f"established[{i}]: proposed 残留（人間による確定待）")
            for cid in e.get("characters", []):
                if type_ok(cid, str) and cid not in ref_ids:
                    r.error(path, f"established[{i}].characters: ID '{cid}' が存在しない")

        ss = data.get("summary_status")
        if ss is not None and ss not in VALID_SUMMARY_STATUS:
            r.error(path, f"summary_status 不正 '{ss}'")
        elif ss == "proposed":
            r.warn(path, "summary_status = proposed（章要約が未確定）")


def validate_meta(project: Path, files: dict[Path, dict], r: Report) -> dict | None:
    meta_path = project / "meta.toml"
    if meta_path not in files:
        r.error(meta_path, "meta.toml が存在しない")
        return None
    data = files[meta_path]
    work = data.get("work")
    if not isinstance(work, dict):
        r.error(meta_path, "[work] セクション必須")
    else:
        check_keys(work, {"title": str, "genre": str, "status": str}, meta_path, "[work]", r)
        if work.get("status") not in VALID_WORK_STATUS:
            r.error(meta_path, f"work.status 不正 '{work.get('status')}'")
    chapters = data.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        r.error(meta_path, "[[chapters]] 必須・1件以上")
        return data
    prev: int | None = None
    for i, c in enumerate(chapters):
        if not isinstance(c, dict):
            r.error(meta_path, f"chapters[{i}] がテーブルでない")
            continue
        check_keys(c, {"number": int, "plot": str}, meta_path, f"chapters[{i}]", r)
        num = c.get("number")
        if type_ok(num, int):
            if prev is not None and num <= prev:
                r.error(meta_path, f"chapters[{i}]: 章番号逆転/重複 ({prev} → {num})")
            prev = num
        rel = c.get("plot")
        if type_ok(rel, str):
            target = project / rel
            if not target.is_file():
                r.error(meta_path, f"chapters[{i}].plot: '{rel}' が存在しない")
            elif target.resolve() not in {f.resolve() for f in files}:
                r.error(meta_path, f"chapters[{i}].plot: '{rel}' が構文エラーでロード失敗")
        st = c.get("status")
        if st is not None and st not in VALID_CHAPTER_STATUS:
            r.error(meta_path, f"chapters[{i}]: status 不正 '{st}'")
    return data


# ---------------------------------------------------------------- index

def build_index(chars, worlds, plots) -> list[str]:
    out = [f"{'ID':<11} 種別   名称"]
    for _, d in chars:
        out.append(f"{d.get('id', '?'):<11} chara  {d.get('name_ja', '')}")
    for _, d in worlds:
        out.append(f"{d.get('id', '?'):<11} world  {d.get('title', '')}")
    for _, d in plots:
        out.append(f"{d.get('id', '?'):<11} plot   ch{d.get('chapter', '?')}: {d.get('title', '')}")
    return out


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="novel2agent-jp 設定検証")
    ap.add_argument("--project-dir", required=True)
    ap.add_argument("--index", action="store_true", help="ID→名称一覧のみ出力")
    args = ap.parse_args()

    project = Path(args.project_dir)
    if not project.is_dir():
        print(f"{ERR} project-dir が存在しない: {project}")
        return 1

    files, parse_errors = load_all(project)
    chars = by_prefix(files, "chara")
    worlds = by_prefix(files, "world")
    plots = by_prefix(files, "plot")

    if args.index:
        for line in build_index(chars, worlds, plots):
            print(line)
        return 0

    r = Report()
    for path, err in parse_errors:
        print(f"{ERR} {path.name}: TOML 構文エラー: {err}")
        r.error(path, "構文エラーのためこのファイルは検証不能")

    chara_ids = validate_characters(chars, r)
    # 参照 ID は構文エラーで欠けた分も考慮 → ロード済み ID の和集合
    ref_ids = chara_ids | {d.get("id") for _, d in worlds if type_ok(d.get("id"), str)}
    validate_worlds(worlds, ref_ids, r)
    validate_plots(plots, ref_ids, r)
    validate_meta(project, files, r)

    print()
    print(f"== 検証結果 ({len(files)} TOML ファイル) ==")
    for line in r.errors:
        print(line)
    for line in r.warnings:
        print(line)
    print(f"\nエラー {len(r.errors)} 件 / 警告 {len(r.warnings)} 件")
    return 0 if not r.errors else 1


if __name__ == "__main__":
    sys.exit(main())
