# 企画フェーズ（TOML 版）

企画 → 世界観 → キャラ → プロットの順に作る。すべての構造化データは TOML に書き、本文は `novel/` にのみ書く。

## 0. プロジェクト初期化

雛形は `scripts/init.py` で生成する（手作業でのディレクトリ作成は省略ミスの元）:

```bash
python scripts/init.py --project-dir <path>
```

既存 `meta.toml` がある場合は上書きしない（エラーで停止）。生成物:

```
project/
├── proposal.md        # 企画書（Markdown のまま・雛形）
├── meta.toml          # 章の唯一の目次・雛形
├── AGENTS.md          # 文体規則・禁止事項（作品の憲法）・雛形
├── .gitignore         # .context/ を除外
├── production-log.toml # 制作ログ（追記専用。なぜ変えたか・却下した案）
├── character/         # chara-NNN.toml
├── worldbuilding/     # world-NNN.toml
├── plot/              # plot-chNN.toml
├── novel/             # chNN.md（本文のみ）
└── .context/          # pack.py 生成物（.gitignore）
```

必ずこの順で作る。スキーマの必須キーは `schema/toml-schema.md` を正とする。

## 0.5 最初に一度 validate を回す

空の `meta.toml` を作ったら、まず検証を通して雛形の形を確認する。

```bash
python scripts/validate.py --project-dir <project>
```

構造エラーはこの段階で潰す。以後、ファイルを増やすたびに随時回す。

## 1. proposal.md（Markdown のまま）

項目：タイトル（仮）／ターゲット層／ジャンル／想定プラットフォーム／長さ／あらすじ 300〜500 字／テーマ・モチーフ／登場人物一覧／章構成のアウトライン／**感情曲線**（章ごとのピーク強度・支配的感情・曲線形状）。

作成後にユーザへ全文提示し、承認を得てから次へ。数値は目安であり、シーン要求に応じて調整可。

### proposal の承認状態（必須）

`proposal.md` 冒頭に状態行を置く（YAML front matter 相当）:

```
proposal_status: proposed
```

- **`proposed` の間は TOML 進行（worldbuilding 以降）に入らない**
- 全文提示 → ユーザが明示的に承認 → `proposal_status: confirmed` に更新
- **企画書を後から変更した場合は同期チェック**: ジャンル・登場人物・舞台・関係性など変更前の要素を proposal.md 全文から検索し、古い表現を削除/書き換える（例: 当初「淡い恋愛」だったものを友情ものに変更したら、その表現が残っていないか確認する。未使用の舞台描写も同様）

感情曲線の記入例：

| 章 | ピーク強度 | 支配的感情 | 曲線形状 |
|----|-----------|-----------|---------|
| 第1章 | 40% | 緊張・抑圧 | 平坦な抑制→終盤で上昇 |
| 第2章 | 80% | 葛藤・悲しみ | 再会の衝撃(70%)→頂点(80%)→沈黙の下降 |
| 第3章 | 100% | 解放・希望 | 急上昇→カタルシス→静かな終幕 |

### 企画が定まらないときの提案材料

作りたい作品がない、または曖昧なときにだけ、次のどれかを一つ提案する。決まっているときは使わない。

- 二つの遠い素材の足し算。「もし〜だったら、しかも〜」の形で、離れた二つを組み合わせたものを企画の核にする。「さらに」で足すと説明的になるので「しかも」で足す
- テーマを後から見つける。テーマ欄を「（仮）執筆後に確定」と注記して進め、七〜八割書いた時点で「この作品の人物たちは皆〜している」という一文が浮かんだらそれをテーマとし、寄与しない場面を削る。`proposal_status` は通常どおり confirmed にしてよい（テーマの確定と企画の確定は別）
- 制約から始める。想定プラットフォーム、文字数、章数、締切、扱える題材の範囲を先に固定し、制約を起点に発想する。自由に書いてよい、が最も書きにくい
- 梗概を人に試す。ユーザに「一、二文で人に話せますか」と聞く。話した反応が薄ければ捨てる提案をする。「つまらない」と言われたら「どこが」を聞くよう促す（エージェントはユーザの代わりに反応を作らない）

## 2. 世界観（worldbuilding/world-NNN.toml）

世界設定が土台。キャラの所属・能力・服装はここから導かれるため必ず先に作る。

- 基本設定は `content` の散文（`'''`複数行リテラル）
- 構造化できる部分（組織一覧・年表等）はテーブル/配列で併用可
- **制約リスト `[[constraints]]` を必ず作る**：この世界に「存在しない語彙」「キャラの知識範囲外」を明示する。推敲フェーズ（Phase B）の照合対象になる

```toml
id = "world-001"
title = "基本設定"
kind = "core"                       # core / geography / rules / glossary
content = '''大正12年〜昭和8年の日本が舞台。魔法は存在しない。'''

[[constraints]]
kind = "forbidden_words"
words = ["スマホ", "SNS", "オッケー", "ググる"]
note = "大正〜昭和初期のため使用禁止"

[[constraints]]
kind = "unknown_to"
target = "chara-003"
words = ["化学用語", "英語"]
note = "山育ちのため知らない"
```

## 3. キャラ（character/chara-NNN.toml）

テンプレートは `references/character-template.md`、発想の手順は `references/character-design-guide.md`。必須キーのみスキーマが検証し、追加キーは自由。

### 3-0. 名前を先に決める

キャラを書き始める前に、全キャラの `name_ja` / `name_ruby` の候補を先に出す。

- 候補を 2〜3 ずつ出してユーザに選ばせる。名前が決まると `first_person` / `speech_style`（口調）が安定し、後の修正が減る
- 未決の間は `name_ja = "TBD 桜井"` のように書き、**TBD が残ったままプロット（§4）へ進まない**。validate が警告する
- 強い却下理由があった名前は `production-log.toml` に `kind = "reject"` で残す（同じ案を再提案しないため）

```toml
id = "chara-001"
name_ja = "桜井美咲"
name_ruby = "さくらい みさき"       # 初出ふりがな検証用
role = "protagonist"

[basic]
gender = "female"
age = 19
first_person = "私"                 # 一人称検証用
speech_style = "丁寧語"

[appearance]                        # 画像生成と執筆の両方の安定性を左右する
hair = "黒髪ロングストレート"
outfit = "白と金の聖女服"

[[relations]]
target = "chara-002"                # 存在チェック対象。# コメントで人間向け名前を併記可
kind = "学友"
emotion = "信頼"

[[versions]]                        # 章またぎ変化はここに一元化（旧: バージョン別 .md ファイル）
from_chapter = 3
age = 20
note = "覚醒後。制服が黒い戦闘服に"
```

規則：

- 章またぎの大きな変化（悪堕ち・所属変更）は `[[versions]]` に変更キーのみ書く。全項目の再記述はしない
- `[basic]` 配下のキー（age 等）を versions に書くと pack.py が `[basic]` に反映する（schema §1）
- 1 キャラ 1 ファイル。章またぎの変化は `[[versions]]` に書く

## 4. プロット（plot/plot-chNN.toml）

1 章 1 ファイル。シーン本文は**ここに書かない**（`novel/` のみ本文）。

```toml
id = "plot-ch01"
chapter = 1
title = "導入"
peak_intensity = 40                 # proposal.md の感情曲線と一致させる
pov = "chara-001"
summary = ""                        # 執筆後に LLM が proposed で記入
summary_status = "proposed"

[[scenes]]
title = "引っ越し"
location = "臼井駅"
time = "夕方・秋"
pov = "chara-001"
characters = ["chara-001", "chara-002"]
content = '''荷物の中から古い日記が出てくる。美咲はページを開けず箱に戻す。'''  # 演出指示
emotion_peak = "静かな導入"

[[foreshadowing]]
id = "fs-001"
content = "荷物から出た古い日記"
resolve_chapter = 3                 # 回収予定章（必須）。実績は resolved_at = 3（未回収は省略）

[[established]]
content = "美咲が臼井市に引っ越した"
status = "proposed"                 # 推敲完了時に人間が confirmed へ
```

シーン雛形の必須：title / location / pov / characters / content（演出）。`time`・`emotion_peak`・キー台詞は推奨。

## 5. meta.toml（章の唯一の目次）

```toml
[work]
title = "作品タイトル"
genre = "現代ファンタジー"
status = "planning"                 # planning / writing / revision / complete

[[chapters]]
number = 1
plot = "plot/plot-ch01.toml"        # validate が存在チェック
novel = "novel/ch01.md"             # 未執筆は省略
status = "draft"                    # draft / written / revised / confirmed
```

章順はこの `[[chapters]]` 記述順で決まる。ファイル名依存の探索はしない。

## 6. AGENTS.md（作品の憲法）

文体規則・禁止事項・シリーズ注意点を 1 本にまとめる。キャラ初出時はふりがなを添える等の規則はここに。

> エージェント非依存の注意：Claude Code は `AGENTS.md` を読まない。`CLAUDE.md` に「AGENTS.md を読め」の 1 行のみ置く運用（goose は `.goosehints` 同様）。

## 7. 最終確認

1. `python scripts/validate.py --project-dir <project>` → エラー 0
2. `python scripts/validate.py --project-dir <project> --index` → ID↔名称の一覧が意図通り
3. ユーザに全ファイル一覧と `--index` 出力を提示し、修正指示を待つ
4. 企画段階で proposal.md の内容を変えた、または案を却下した場合、`production-log.toml` に記録したか

設定はすべて TOML に残る。
