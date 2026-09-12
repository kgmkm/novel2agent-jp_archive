# novel2hermes-jp アップデート計画 v2

## 概要

小説設定管理を **vecmemori 依存のデュアルストレージ** から、**ファイル正規原典 + Python による決定論的文脈生成** へ全面転換する。

```
TOML（設定・構造化データ）
  ↓ validate.py（機械検証）
  ↓ pack.py（文脈パック生成）
.context/chNN.md（LLM に渡す Markdown・再生成可能）
```

## 背景：なぜ転換するか

1. **トークンコスト**：vecmemori 検索は「探しに行く」方式のため取得漏れが起き、逆に全件読みでは高コスト。必要な設定だけを決定論的にコンテキストへ載せる方が安く正確。
2. **同期ずれ**：.md と vecmemori の二重管理は「どちらが最新か」問題を常に抱える。ファイル1本化で同期処理自体が不要になる。
3. **エージェント非依存**：生成物が Markdown なら Hermes 以外（opencode / goose / Claude Code 等）でも同じ原稿を扱える。

## 確定事項一覧

| # | 項目 | 決定内容 |
|---|------|---------|
| 1 | vecmemori | **完全廃止**。関連スキル（jp-novel-qa 等）も依存を外し novel2hermes-jp に統合 |
| 2 | proposal.md | Markdown のまま |
| 3 | plot | **TOML 1本化**（章ごと1ファイル。シーン本文は `'''` 複数行リテラル） |
| 4 | character / worldbuilding | TOML 化 |
| 5 | novel/ | 本文 Markdown のみ（plot に本文を重複保存しない） |
| 6 | continuity/ 台帳 | **新設しない**。属性変更→キャラ TOML の `[[versions]]`、出来事→章 TOML の `[[established]]` |
| 7 | 不確定事実の扱い | LLM が `status = "proposed"` で追記 → 推敲完了時に人間が `"confirmed"` に変更。validate は proposed 残留で警告 |
| 8 | 伏線回収 | `[[foreshadowing]]` に `resolved_at = N` を追記する一元化。established には書かない |
| 9 | 章要約 | plot TOML の `summary` フィールド。LLM proposed → 人間 confirmed の流れで生成 |
| 10 | 文脈パック | `.context/chNN.md` に出力。**.gitignore（再生成可能な派生物のため）**。pack.py 実行ごとに上書き |
| 11 | proposed 残章の扱い | pack.py は **未確定と明示して含める**（除外すると矛盾の元） |
| 12 | 前章本文 | 直前1章は全文、それ以前は章要約。`--budget` 引数で総量制御（既定100Kトークン相当、超過時は直前章を末尾から削る） |
| 13 | ID | 連番+種類別プレフィックス（`chara-001` / `plot-001` / `fs-001` / `world-001`）。ファイル名=ID を validator が強制 |
| 14 | ID 可読性 | (a) ファイル名=ID強制 (b) 参照箇所に `# 佐藤翔太` コメント併記可 (c) `validate.py --index` で ID→名称一覧 |
| 15 | 章範囲表現 | 文字列ではなく数値：`from_chapter = 1` / `to_chapter = 2`（終端未定は省略） |
| 16 | meta.toml | 章の唯一の目次。ファイル名順に依存しない |
| 17 | シリーズ化 | v4 スコープは1作品。将来用に (a) ID はシリーズ内一意 (b) 探索パスを「作品ディレクトリ→その親」の2段にする。シリーズ横断変化は後から `from_work = "w02"` を optional 追加 |
| 18 | スクリプト | 全て TOML 前提に書き換え。読み込みは標準 `tomllib`（Python 3.11+）。書き込みが必要な場合のみ `tomli-w` |
| 19 | validator | 値を推測で埋めない。構造エラーは停止、警告系は明示出力 |

## ディレクトリ構成（確定）

```
project/
├── proposal.md
├── meta.toml                  # 章の目次・ステータス
├── AGENTS.md                  # 文体規則・禁止事項（作品の憲法）
├── character/
│   ├── chara-001.toml
│   └── chara-002.toml
├── worldbuilding/
│   ├── world-001.toml         # 基本設定
│   └── world-002.toml         # 制約リスト等
├── plot/
│   ├── plot-ch01.toml         # [[scenes]] [[foreshadowing]] [[established]] summary
│   └── plot-ch02.toml
├── novel/
│   ├── ch01.md                # 本文のみ
│   └── ch02.md
├── .context/                  # pack.py 生成物（.gitignore）
│   └── ch03.md
└── schema/                    # スキーマ定義（toml-schema.md）
```

## 実装タスク

### P0：設計確定（本ドキュメントで完了）
### P1：最小実装
1. `schema/toml-schema.md`（別ファイルで作成済）
2. `scripts/validate.py` — 構文・必須キー・型・ID重複・参照存在・ファイル名=ID・versions範囲・伏線対応・proposed警告・`--index` 一覧
3. `scripts/pack.py` — 第N章用コンテキスト生成。登場キャラ（from_chapter ≦ N の versions 解決済）・世界制約・前章全文 or 要約・未回収伏線・established（proposed は明示）・`--budget` 制御・established ロールアップ・`--check` 鮮度チェック。**受け入れ条件**：versions 重複解決・伏線抽出漏れなし・budget 削り順遵守・ロールアップで proposed 残留、の4点をテストで担保（新構成では pack.py が唯一の情報源＝単一点のため必須）
4. 既存データ移行 — **自動変換ツールは作らない**。vecmemori DB の fact は検索用に断片化しており機械写しは粗い出力になるため、既存プロジェクトは「手で TOML に書き直す＝設定見直し」とする。新規プロジェクトは最初から TOML で作成

### P2：ワークフロー更新
1. `writing-workflow.md`：先頭を `validate.py → pack.py --check（鮮度確認）→ 必要なら pack.py 再生成 → .context/chNN.md を読んで執筆` に固定。vecmemori・session_search・/compress 依存を全削除
2. `planning-workflow.md`：fact_store / memory(action) の手順を全削除、TOML 作成手順に置換
3. `revision-workflow.md`：推敲完了時に proposed → confirmed 変更手順を追加
4. `character-template.md`：TOML テンプレートに全面改訂
5. `multi-agent-memory.md` / `fact-store-reference.md`：削除
6. `SKILL.md`：エージェント非依存化。Hermes 固有手順（venv パス・ZIP復旧等）は `references/hermes-setup.md` へ隔離

### P3：品質検証
1. キャラテンプレ全項目の TOML 移行可能性確認
2. versions の章切替・伏線張り/回収検証の動作確認
3. Hermes 以外のエージェントで .context から執筆できるか確認
4. pixiv_export.py 等の既存スクリプトを novel/ 構造前提に改修

## Hermes 依存の切り離し（他エージェント対応）

vecmemori 廃止に加え、Hermes 固有机能の依存を以下の5層で除去・隔離する。TOML 化と同じアップデートに同梱する。

### 層1：スキルの発火条件・自己参照
- `SKILL.md` の description を「Hermes Agent」前提から「日本語小説制作」前提に書き換え（他エージェントがスキルを選べるようにする最初の1行）
- `skill_view(name=...)` 前提の記述、ZIP 復旧手順（`$HERMES_HOME/skills/` 固定）を削除または hermes-setup.md へ隔離

### 層2：Hermes 固有ツール呼び出しの置き換え

| 依存箇所 | 現行 | 置き換え方針 |
|---------|------|------------|
| `session_search` ×5（writing 2-0、revision 推奨ツール表、illustration-guide） | 過去セッション検索で復旧 | **meta.toml の status + plot TOML の established/summary で代替**。廃止 |
| `memory(action="add")`（planning 1-5） | ビルトインメモリへ核心設定を保存 | **削除**。meta.toml に集約 |
| `/compress`（revision 冒頭、README） | Hermes スラッシュコマンド | 趣旨（「文脈が長くなったら圧縮を提案」）だけ残し、コマンド名はエージェント別対応表に逃がす（Hermes `/compress`、Claude Code `/compact`、goose `/summarize` 等） |
| `write_file` / `read_file` / `patch` ×15 | ツール名は Hermes 固有 | **優先度低**。疑似コードとして実害小さいため現状維持（他エージェントでも意味は通じる） |

### 層3：環境セットアップの隔離
- `project-init.md` はほぼ全面 Hermes 依存（`hermes config set`、`hermes tools enable`、venv パス、`/reset`）。vecmemori 廃止で Step1〜6 は消滅。**残る Step7（ツール有効化）は `references/hermes-setup.md` へ隔離**
- SKILL.md 実行環境セクションの作者環境絶対パス直書き（Windows venv パス）は汎用化して hermes-setup.md へ移動

### 層4：スクリプト
- `scripts/list-models.py`：`~/.hermes/auth.json` / `.env` から認証を読む Hermes 依存スクリプト。**MoA 側（旧 fake-moa 後継）へ移管し、novel2hermes からは削除**
- `scripts/pixiv_export.py` / `vfm_to_pixiv.py`：Hermes 非依存のため維持（TOML 構造前提への改修のみ）

### 層5：MoA 周辺
- `moa-manual-orchestration.md` の手動手順が `hermes chat -q -m MODEL` / `hermes auth add` 前提。**プロンプト本文（4視点の指示文）だけを残し、「fake-moa 後継ツールが無い環境では任意の方法で別モデルに投げよ」とする**形でエージェント非依存化
- **「fake-moa」名称の廃止**：エージェント非依存化に伴い名称が不適当になるため、汎用的な名称に改称（例：`moa-orchestrator` / `multi-llm-moa`）。後継ツールの新名称は別途決定

### Hermes 非依存だが要確認
- **AGENTS.md 自動読込**：Hermes / opencode / Codex は読むが、Claude Code は `CLAUDE.md`、goose は `.goosehints`。作品ガイドは AGENTS.md 1本を正とし、他エージェント用ファイルには「AGENTS.md を読め」の1行のみ記述する運用
- ComfyUI 連携は Hermes ではなく ComfyUI 依存のため対象外

### 作業まとめ（4本）
1. SKILL.md description 修正
2. session_search / memory / compress の3種置き換え
3. project-init と手動 MoA の Hermes 部分を `references/hermes-setup.md` へ隔離
4. `list-models.py` の移管＋「fake-moa」改称

## リポジトリ移行計画（改名 + 別リポジトリ化）

本改定は「バージョンアップ」ではなく思想の転換（デュアルストレージ → ファイル一元化、Hermes 依存 → エージェント非依存）のため、スキル名を変更し別リポジトリとして開発する。

### 新スキル

- **名称**：`novel2agent-jp`（`novel2epub-jp` との命名一貫性。agent は汎用語＝エージェント非依存の思想と合致）
- **新リポジトリ**：`kgmkm/novel2agent-jp`（仮）
- **description（front matter）の1文目で誤読を潰す**（novel2agent＝「novel を agent に変換」とも読めるため）：

```yaml
description: "Use when writing Japanese novels with AI coding agents (Hermes, Claude Code, opencode, goose). File-based, agent-agnostic workflow: settings in TOML, deterministic context packs, validation scripts."
```

他エージェントは description でスキルを選択するため、Hermes 以外の名を列挙することが発火率に直結する。

### 旧スキル `novel2hermes-jp` の扱い

GitHub の Archive（read-only）化を採用する。**Archive しても clone / pull / fork / ZIP ダウンロードは可能**（不可なのは push・Issue・PR・設定変更のみ）。そのため旧版を参照・利用したいユーザーへの影響はなく、読み取り専用で凍結できる。

### 移行手順（順序固定）

1. `novel2agent-jp` を新リポジトリとして公開（利用可能な状態にする）
2. 旧 `novel2hermes-jp` に **DEPRECATED 最終リリース**を1回だけ行う
   - README.md を「開発終了・後継は novel2agent-jp」への誘導のみに書き換え
   - **SKILL.md の description も `DEPRECATED: novel2agent-jp に移行。詳細は <URL>` に書き換え**（ローカルに旧スキルが残っているユーザー＝LLM が旧 SKILL.md を読み込んだ瞬間に移行を察知できるようにするため）
3. 旧リポジトリを **Archive（read-only）化**

この順序により、新規ユーザーのクローン経路を確保してから旧版を凍結できる。README 誘導は新規インストールに、SKILL.md description 書き換えは「ローカル保存済み旧スキル」に、それぞれ効く。

### 関連リポジトリの整理

| リポジトリ | 方針 |
|-----------|------|
| `kgmkm/novel2agent-jp` | **新設**。本計画の成果物すべてをここに集約 |
| `kgmkm/novel2hermes-jp` | DEPRECATED 最終リリース後、**Archive** |
| `kgmkm/vecmemori-plus` | **リポジトリ自体はそのまま存続**。スキル（novel2hermes / novel2agent 両方）からの参照は削除。他用途（マルチエージェント共有メモリ）では利用可 |
| fake-moa（後継・改称予定） | `novel2agent-jp` とは別リポジトリで開発。名称は汎用的なものに改称（例：`moa-orchestrator` / `multi-llm-moa`）。novel2agent-jp からは「存在すれば使う」前提の参照に留める |

## 旧ドキュメントとの関係

本ファイルは `novel2hermesアップデート計画_toml転換.md` と `novel2hermes-toml化追加質問.md` の内容を統合・確定したもの。旧2ファイルは本ファイルとスキーマ定義書で吸収済み。
