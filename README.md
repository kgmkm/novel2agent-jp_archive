# novel2agent-jp

**AI コーディングエージェントで日本語小説を書くためのスキル**。旧スキル `novel2hermes_jp` の後継。

設定を **TOML ファイルに正規化し、Python スクリプトで決定論的に検証・文脈パック生成する**方式。ベクトルストア（vecmemori 等）やエージェント固有のメモリに依存しない。生成物は Markdown なので、Hermes / Claude Code / opencode / goose など**どのエージェントでも同じ設定を扱える**。

```
TOML（キャラ・世界観・プロット）
  ↓ scripts/validate.py（機械検証）
  ↓ scripts/pack.py（文脈パック生成）
.context/chNN.md（LLM に渡す Markdown。再生成可能）
```

## 特徴

- **企画 → 執筆 → 推敲** — 編集者と小説家の分業体制を再現
- **TOML で正規化** — キャラ・世界観・プロットを構造化データとして管理。人間が編集しやすく、機械が検証しやすい
- **ファイル単一情報源** — メモリ DB への二重同期を廃止。設定は TOML だけを見ればよい（同期漏れ・隠れた古い記憶の事故が消える）
- **決定論的文脈生成** — `pack.py` が「この章を書くのに必要な設定」を自動で束ねる。LLM に「探させる」のではなく「最初から全部渡す」
- **章またぎ変化を `[[versions]]` で追跡** — 悪堕ち・成長・所属変更など、1キャラ複数の時点を1ファイルで管理
- **`proposed` / `confirmed` の二段階確定** — LLM が「たぶんこれ」と書いた未確定設定は `proposed` で追記され、人間が承認してから `confirmed` に。勝手に確定扱いされる事故を防ぐ
- **複数 LLM による推敲** — 論理・文体・時代考証・読者視点の 4 エージェント構成。MoA（Mixture of Agents）で単一モデルの偏向を排除
- **40項目超の高解像度キャラテンプレート** — 画像生成（ComfyUI 等）との連携を前提とした外見指定
- **キャラ発想ガイド** — 欠点先行・名前先決め・三層チェック（`references/character-design-guide.md`）。設計上の役割（`screen_time` / `function`）は機械検証される
- **制作ログ `production-log.toml`** — 「なぜ変えたか・何を却下したか」を追記専用で残す。git と併用し、`validate.py --log` で読む
- **縦書きEPUB/PDF化** — [novel2epub-jp](https://github.com/kgmkm/novel2epub-jp) で A6文庫判へ変換可能
- **ジャンル不問** — ファンタジー / SF / ミステリ / 恋愛 / 青春 / 歴史 / ホラー etc.

## 作例

[【小説】妖狐は、嗤う](https://note.com/kagami_kami/n/n4a2a7b9f0d38) note.com 約18,000字 4章構成（※旧スキル `novel2hermes_jp` で制作）

```
企画・執筆・ディレクションLLM: opencode/deepseek-v4-pro
推敲LLM: opencode/mimo-v2.5-pro, opencode/glm-5.1, nous-portal/deepseek-v4-flash
挿絵画像生成ツール: ComfyUI + anima_v10
表紙画像生成ツール: hailuo + GPT-Image-2
プロンプト生成・画像推敲LLM: opencode/qwen3.6-plus
```

## 導入

### 前提

- **AI コーディングエージェント** — Hermes / Claude Code / opencode / goose など、任意の1つ
- **Python 3.11+** — スクリプトの実行に必須（validate.py / pack.py）
- **LLM プロバイダ** — エージェントに最低1つ設定済みであること。推敲フェーズでは複数プロバイダの併用を推奨（全エージェントが異なる LLM であると単一モデルの偏向を排除できる）
- [novel2epub-jp](https://github.com/kgmkm/novel2epub-jp) Markdown小説 → A6縦書きPDF/EPUB変換スキル（出版フェーズで使用）

### インストール

このリポジトリをエージェントのスキルディレクトリに配置する。

```bash
# Hermes の場合
git clone https://github.com/kgmkm/novel2agent-jp ~/.hermes/profiles/<あなた>/skills/novel2agent-jp

# Claude Code / その他の場合は、各エージェントのスキル/プラグインディレクトリに配置
```

### クイックスタート（5分で動作確認）

リポジトリには最小構成のサンプルプロジェクト `example/` を同梱しています。

```bash
git clone https://github.com/kgmkm/novel2agent-jp
cd novel2agent-jp

# 1. サンプルプロジェクトで検証
python scripts/validate.py --project-dir example/sample-novel

# 2. 文脈パック生成
python scripts/pack.py --project-dir example/sample-novel --chapter 1

# 3. 生成された .context/ch01.md を読んでみる
cat example/sample-novel/.context/ch01.md
```

これで「TOML → validate → pack → LLM に渡す Markdown」の一連の流れが確認できます。

## 使い方

1. エージェントを起動し、スキル `novel2agent-jp` を読み込む
2. 「企画から始めて」→ 企画フェーズ開始。proposal.md → 世界観 TOML → キャラ TOML → プロット TOML の順に作成
3. 「第1章を書いて」→ 執筆フェーズ開始。冒頭で `validate.py → pack.py` を回して `.context/ch01.md` を LLM に読ませ、忠実に執筆
4. 「推敲して」→ 複数 LLM（MoA）が利用できる環境なら、論理 / 文体 / 時代考証 / 読者視点の 4 視点で整合性検証 → 読者視点評価

詳細は [SKILL.md](SKILL.md) および `references/` の各ワークフローを参照。

## Key Workflow

制作は 5 フェーズ。各フェーズの手順書は `references/` の各ワークフローを正とする。

1. **企画フェーズ** — `proposal.md` → 世界観（`worldbuilding/`）→ キャラ（`character/`）→ プロット（`plot/`）。キャラは `character-design-guide.md` の手順（欠点を先に決める・名前を先に決める）で作り、各段階で `validate.py` を回す（`references/planning-workflow.md`）
2. **プロット検証（執筆前）** — タイムライン・キャラの知識状態・伏線の張り→回収を確認する（Phase A。`references/revision-workflow.md`）
3. **執筆フェーズ** — 章ごとに `validate.py → pack.py --check → 必要なら pack.py → .context/chNN.md を読んで執筆`。シーンの演出・感情曲線・五感ローテーション・比喩はパックの指示に従う。保存直後に `check_prose.py`（`references/writing-workflow.md`）
4. **推敲（revision）** — Phase B（整合性・ミクロ）→ Phase C（読者視点・マクロ。C-1 の 6 問 → C-2 キャラ点検 → C-3 感想）。複数 LLM を使える環境では論理 / 文体 / 時代考証 / 読者視点の 4 視点 MoA（手順: `references/moa-manual-orchestration.md`）。完了時に proposed → confirmed の確定を行う
5. **エクスポート** — `pixiv_export.py` で投稿用に変換。[novel2epub-jp](https://github.com/kgmkm/novel2epub-jp) で縦書き PDF/EPUB 化

- 執筆・推敲で既定の決定を変えた場合、または案を却下した場合は `production-log.toml` に記録する（追記専用）
- **フェーズ移行時および会話が長くなった際は、コンテキスト圧縮を提案すること。**（Hermes なら `/compress`、Claude Code なら `/compact`、goose なら `/summarize`。詳細: `references/revision-workflow.md`「コンテキスト管理」）

## 人類側Tips

### 【最重要】TOML（設定）を人間が修正したら、Agentに報告しよう！

このシステムでは、設定の正規原典は TOML ファイルのみです。AI は設定を TOML に書き、執筆時は `pack.py` で生成された `.context/chNN.md` を読みます。

ただし、**人間が TOML を直接編集したかどうかを自動検知する機能はありません**（常駐監視はトークンコストと時間が嵩むため不採用）。キャラの年齢を直した、世界観を補強した、プロットを変えた——などの場合は、Agent に「TOML を更新したので validate と pack を回してください」と報告してください。そうすると Agent が検証と再生成を行い、次の執筆に反映します。

### 作業の切れ目に長文コンテキストを圧縮しよう

話のピンポンが長くなると LLM の性能が落ちます。作業の切れ目（例：キャラ設定が終わってプロットに入る手前）に、エージェントのコンテキスト圧縮機能を使いましょう（Hermes なら `/compress`、Claude Code なら `/compact`、goose なら `/summarize` 等）。スキル側にも、切れ目で圧縮を提案するよう伝えています。

### 世界観・キャラ・プロットは納得いくまで編集しよう（そして報告！）

だいたい上記の順にまとめてくれますが、ここは AI にまかせっぱなしにせず、必ず人間が確認しましょう。「あれ？」「ちょっとイメージ違う」が出た場合、その場で TOML を直して AI に報告するか、AI に違和感を伝えて変えてもらってください。プロットが固まってから遡って世界観やキャラを直すのも全然アリです。この3つの出来が、小説の品質を決定します。ここ一番の頑張りどころなのでちゃんと読め！なおせ！

### プロット完成後は、小説を……書かずに推敲を依頼しよう！

プロットが全部できた段階で、流れ的に矛盾が発生することがよくあります。AI が書いたからという話ではなく、人類が書いてても普通に起こります。人間そんなに頭よくねえもん。なので、ここで推敲を依頼してください。プロット段階に潜むバグが見つかるかも？

### 執筆中でもプロットなおそう！

執筆中に小説から微妙な臭いを感じたら、それは LLM が悪いというより、プロット・設定・企画を疑った方がいいです。執筆の途中でも意見を挟み、プロットの修正を提案しましょう。設定側に齟齬がある場合も直してください（このタイミングの場合、直接編集よりも一旦エージェントに相談するほうがオススメ。TOML の整合管理はエージェントの方が正確です）。

### LLM にこだわろう！

とはいえ、LLM そのものが悪いケースもあります。ちゃんと書くなら、超激安みたいなのは選ばない方がいいです。じゃあ何を選べば……わからねえ……

が、それをエージェントに調べさせる方法があります。「小説など文章を書くのにオススメな LLM モデルを、直近6か月のネットの反応を検索して教えて」と聞いてみてください。X を検索させるのも効果的です。

### 変更の理由と却下案は production-log.toml に残る

プロジェクトは git 管理を推奨します。git は「何がいつ変わったか」を持ち、`production-log.toml` は「なぜ変えたか・何を却下したか」を持ちます。初回の決定は書きません（proposal.md と TOML 自体が記録です）。変えた時、却下した時にだけ追記されます。人間が読むときは:

```bash
python scripts/validate.py --project-dir <project> --log
python scripts/validate.py --project-dir <project> --log --affects plot-ch03
```

## このリポジトリのファイル構成

```
novel2agent-jp/
├── SKILL.md                     ← メインスキル定義
├── README.md                    ← このファイル
├── LICENSE                      ← MIT
├── schema/
│   └── toml-schema.md           ← TOML スキーマ定義（必須キー・検証項目・pack.py 仕様）
├── scripts/
│   ├── validate.py              ← 設定検証（構文・必須キー・ID・参照整合・制作ログ）
│   ├── pack.py                  ← 文脈パック生成（章ごとの LLM 渡し用 Markdown）
│   ├── check_prose.py           ← 本文品質検査（空本文・禁止語彙・全角空白）
│   ├── init.py                  ← プロジェクト雛形生成
│   ├── pixiv_export.py          ← pixiv 小説投稿用変換
│   ├── vfm_to_pixiv.py          ← 縦読み記法 → pixiv 変換
│   └── tests/                   ← スクリプトのテスト
├── references/
│   ├── planning-workflow.md     ← 企画フェーズ（世界観→キャラ→プロット）
│   ├── writing-workflow.md      ← 執筆フェーズ（pack → 執筆 → TOML 反映）
│   ├── revision-workflow.md     ← 推敲フェーズ（Phase A/B/C + MoA 4 視点）
│   ├── moa-manual-orchestration.md ← 4 視点 MoA の実行手順（エージェント非依存）
│   ├── character-template.md    ← キャラ TOML テンプレート（40 項目超）
│   ├── character-design-guide.md ← キャラ発想ガイド（欠点先行・名前先決め）
│   ├── metaphor-guide.md        ← 比喩ガイド（クリシェ回避）
│   ├── sensory-rotation.md      ← 五感ローテーションガイド
│   ├── vfm-to-pixiv-workflow.md ← 縦読み記法 → pixiv ワークフロー
│   └── hermes-setup.md          ← Hermes 固有の環境セットアップ（他エージェントでは不要）
└── example/
    └── sample-novel/            ← 最小構成のサンプルプロジェクト（クローン後すぐに試せる）
        ├── meta.toml
        ├── proposal.md
        ├── AGENTS.md
        ├── character/
        ├── worldbuilding/
        ├── plot/
        └── novel/
```

## 生成される小説プロジェクトの構成（ユーザが作る側）

企画フェーズと執筆フェーズを通じて、プロジェクトディレクトリ直下に以下が生成されます：

```
my-novel-project/
├── proposal.md            ← 企画書（Markdown のまま。あらすじ・テーマ・章構成）
├── meta.toml              ← 章の唯一の目次（章番号・plot/novel パス・status）
├── AGENTS.md              ← 作品固有ガイド（文体・トーン・禁止事項・初出ふりがな規則）
├── production-log.toml    ← 制作ログ（追記専用。なぜ変えたか・却下した案）
│
├── character/             ← キャラ TOML（1キャラ1ファイル）
│   ├── chara-001.toml
│   └── chara-002.toml
│
├── worldbuilding/         ← 世界観 TOML
│   ├── world-001.toml     ← 基本設定
│   └── world-002.toml     ← 制約リスト（存在しない語彙・キャラ知識範囲外）
│
├── plot/                  ← 章ごとのプロット TOML（シーン・伏線・established）
│   ├── plot-ch01.toml
│   └── plot-ch02.toml
│
├── novel/                 ← 小説本文（Markdown。本文はここにのみ書く）
│   ├── ch01.md
│   └── ch02.md
│
└── .context/              ← pack.py 生成物（.gitignore 推奨。再生成可能）
    ├── ch01.md
    └── ch02.md
```

## 旧スキルからの主な変更点

- **vecmemori / ベクトルメモリ廃止** — 設定の正規原典は TOML のみ。二重同期をやめた
- **Hermes 固有ツール依存の除去** — `session_search` / `memory` / `/compress` への直接言及をなくし、エージェント非依存に
- **TOML で正規化** — Markdown テンプレートから TOML へ移行（人間も編集可、機械検証も可）
- **決定論的文脈生成** — LLM に「設定を探させる」旧方式から、`pack.py` が「全部まとめて渡す」新方式へ

## 更新履歴

### v0.3.1（2026-09-16）
- キャラ発想ガイド `references/character-design-guide.md` を新設。設計キー `flaw` / `quirk` / `heat` / `[design].screen_time` / `[[relations]].function`・`no_compromise` / `[motivation].false_belief` を追加
- `role` を protagonist / antagonist / support の 3 値に固定（validate が検査）。仮名（TBD）残留の警告を追加
- 制作ログ `production-log.toml` を新設（schema §8。`validate.py --log`・pack 収録）
- 推敲 Phase C を縮小（C-1 の 6 問 → C-2 キャラ点検 → C-3 感想）。MoA 視点 4 は「はい/いいえ＋根拠」必須に
- MoA 手動オーケストレーション `references/moa-manual-orchestration.md` を新設（エージェント非依存の 5 実行パターン）
- README に Key Workflow を追加。`pack.py` の versions appearance 反映バグ修正・未使用コード削除

### v0.3.0（2026-09-13）
- `check_prose.py`（本文品質検査）・`init.py`（プロジェクト雛形生成）を新設
- `pack.py --check` が章単位の鮮度チェックに対応
- `validate.py` に本文パス存在チェック・proposal 照合・proposed 警告の改善

### v0.2.0（2026-09-13）
- references 5 本を TOML 版で全面改訂、README 全面改訂・example/sample-novel 同梱
- pixiv_export / vfm_to_pixiv を新構造（`novel/chNN.md`）に対応

### v0.1.0（2026-09-13）
- 新スキル骨格（SKILL.md / README / toml-schema）
- `validate.py` / `pack.py` の実装とテスト

## 注意

### AT YOUR OWN RISK: 自己責任で導入してください。

このリポジトリのスキルをインストールしたこと、およびこのスキルを使い生成したコンテンツにより発生した問題の責任所在は、リポジトリオーナーには存在せず、このスキルの使用者に限定されます。

## ライセンス

MIT License — 詳細は [LICENSE](LICENSE) を参照。

## 謝辞

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research
- [ruri-v3](https://huggingface.co/cl-nagoya/ruri-v3-310m) by cl-nagoya（旧スキルの design 参考）
- [葦澤かもめ](https://note.com/ashizawakamome) — 比喩表現など SKILL.md 設計の参考
- [JLREQ（日本語組版処理の要件）](https://github.com/w3c/jlreq) by W3C — 日本語組版ルールの基盤資料。詳細: [novel2epub-jp](https://github.com/kgmkm/novel2epub-jp)
