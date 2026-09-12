---
name: novel2agent-jp
description: "Use when writing Japanese novels with AI coding agents (Hermes, Claude Code, opencode, goose). File-based, agent-agnostic workflow: settings in TOML, deterministic context packs, validation scripts."
version: 0.3.0
---

# novel2agent-jp

日本語小説制作のためのエージェント非依存ワークフロースキル。

## 発火条件

日本語小説の制作・執筆・推敲を AI コーディングエージェントに依頼するとき。

## 仕組み

```
TOML（設定・プロット・キャラ・世界観）
  ↓ scripts/validate.py（機械検証）
  ↓ scripts/pack.py（文脈パック生成）
.context/chNN.md（LLM に渡す Markdown・再生成可能）
```

- 設定はすべて TOML。本文は `novel/chNN.md` にのみ書く
- 属性変更はキャラ TOML の `[[versions]]`、出来事は章 TOML の `[[established]]` に一元化
- LLM の未確定事実は `status = "proposed"` で追記し、人間が `"confirmed"` に変える
- 伏線の回収実績は `[[foreshadowing]]` の `resolved_at` に一本化

## 執筆セッション開始時の固定手順

```
scripts/validate.py → scripts/pack.py --check → 必要なら pack.py 再生成 → .context/chNN.md を読んで執筆
```

## 参照

| ファイル | 読むとき |
|---|---|
| `schema/toml-schema.md` | TOML の必須キー・検証項目・pack.py 出力仕様 |
| `references/planning-workflow.md` | 企画フェーズ（proposal / worldbuilding / character / plot の TOML 作成手順） |
| `references/writing-workflow.md` | 執筆セッションの手順（pack 生成 → 執筆 → TOML 反映） |
| `references/revision-workflow.md` | 推敲フェーズ（Phase A/B/C + MoA 4 視点 + proposed 確定手順） |
| `references/character-template.md` | キャラ TOML の全項目テンプレートと記入例 |
| `references/sensory-rotation.md` | 五感ローテーション（シーンごと視覚以外 2 つ以上） |
| `references/metaphor-guide.md` | 比喩の選び方（クリシェ回避・1〜2 個/シーン） |
| `references/hermes-setup.md` | Hermes 固有の環境セットアップ（他エージェントでは不要） |

## 状態

v0.3.0：v0.2.0 に加え、`check_prose.py`（本文品質検査）・`init.py`（プロジェクト雛形生成）を追加。`pack.py --check` は章単位鮮度チェックに対応。`validate.py` は本文パス存在チェック・proposal 照合・proposed 警告の文言改善を実施。

## 本文保存の鉄則（事故対策）

- **Markdown 段落は空白なし**: 段落頭に全角空白を入れない（編集経路で本文が壊れる実例あり）
- **保存直後に `check_prose.py` を回す**: 本文が空になっていないかを機械で確認してから次へ進む

## Scripts

### `scripts/validate.py` — 設定検証

```bash
python scripts/validate.py --project-dir <project>           # 構造検証（エラー 1 件で exit 1）
python scripts/validate.py --project-dir <project> --index   # ID→名称一覧のみ
```

検証項目は `schema/toml-schema.md` §5。proposed 残留は警告（exit 0）。

### `scripts/pack.py` — コンテキストパック生成

```bash
python scripts/pack.py --project-dir <project> --chapter N            # .context/chNN.md 生成
python scripts/pack.py --project-dir <project> --chapter N --check    # 生成物の鮮度チェックのみ
python scripts/pack.py --project-dir <project> --chapter N --budget 80000
```

出力仕様は `schema/toml-schema.md` §6。未回収伏線は budget でも削らない。

### `scripts/check_prose.py` — 本文品質チェック

```bash
python scripts/check_prose.py --project-dir <project>            # 全章検査
python scripts/check_prose.py --project-dir <project> --chapter N
python scripts/check_prose.py --project-dir <project> --min-chars 200
python scripts/check_prose.py --project-dir <project> --strict   # 警告でも exit 1
```

検査: 本文存在（空本文・最低文字数）／段落頭全角空白／禁止語彙（worldbuilding constraints）／一人称の揺れ／章見出し。**本文保存直後に必ず実行する**。

### `scripts/init.py` — プロジェクト雛形生成

```bash
python scripts/init.py --project-dir <path>
```

ディレクトリ一式 + proposal.md / meta.toml / AGENTS.md / .gitignore の雛形を作る。既存 meta.toml は上書きしない。

### `scripts/pixiv_export.py` — pixiv 投稿用変換

`novel/chNN.md`（旧 `NNN-タイトル.md` も受理）を pixiv 小説投稿用単一ファイルへ統合。

```bash
python scripts/pixiv_export.py --project-dir <project>            # export/pixiv.md に統合
python scripts/pixiv_export.py --project-dir <project> --split    # 50,000字超過時に章分割
python scripts/pixiv_export.py --project-dir <project> --verify   # 本文が改変されていないか差分検証
python scripts/pixiv_export.py --project-dir <project> --check-length
```

### `scripts/vfm_to_pixiv.py` — VFM→pixiv タグ変換

```bash
python scripts/vfm_to_pixiv.py novel/ch01.md -o pixiv/ch01.txt
```

記法対比表は `references/vfm-to-pixiv-workflow.md`。
