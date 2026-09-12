---
name: novel2agent-jp
description: "Use when writing Japanese novels with AI coding agents (Hermes, Claude Code, opencode, goose). File-based, agent-agnostic workflow: settings in TOML, deterministic context packs, validation scripts."
version: 0.2.0
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

v0.2.0：schema 確定 / scripts（validate.py・pack.py＋17 テスト）完成 / references 5 本整備済み。
残課題：pixiv_export 等の既存スクリプトの TOML 構造対応（P3）。
