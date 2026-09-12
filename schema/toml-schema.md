# novel2agent-jp TOML スキーマ定義書

## 0. 共通規則

- **文字コード**：UTF-8
- **ファイル名 = ID**：`chara-001.toml` の `id` は必ず `"chara-001"`。validator が強制する
- **ID 命名**：`{prefix}-{3桁連番}`。prefix は `chara` / `fs` / `world`。シリーズ内で一意
- **plot 章ファイルの例外**：plot のみ章番号を ID に含む `plot-ch{2桁}.toml`（例：`plot-ch01.toml`、id も `"plot-ch01"`）。meta.toml から参照しやすくするための例外。validate.py は両形式でなくこの形式のみを検証する
- **章範囲**：`from_chapter = N`、`to_chapter = M`（整数。終端未定は `to_chapter` を省略）
- **status**：`"proposed"`（LLM提案・未確定）または `"confirmed"`（人間承認済）。省略時は confirmed 扱い。established / summary のみ使用
- **コメント**：ID 参照箇所には `# 桜井美咲` のような人間向けコメントを許可（機械は無視）
- **パーサ**：読込は `tomllib`（Python 3.11+ 標準）。書込が必要な場合のみ `tomli-w`

---

## 1. character（character/chara-NNN.toml）

```toml
id = "chara-001"                    # 必須・ファイル名と一致
name_ja = "桜井美咲"                # 必須
name_ruby = "さくらい みさき"        # 必須（初出ふりがな検証用）
role = "heroine"                    # 必須。protagonist/heroine/rival/mentor/mob 等

[basic]                             # 必須セクション
gender = "female"
age = 19
height_cm = 158
first_person = "私"                 # 必須（一人称検証用）
speech_style = "丁寧語"

[appearance]
hair = "黒髪ロングストレート"
eyes = "ダークブラウン"
outfit = "大学の私服"

[personality]                       # 任意
keywords = ["真面目", "好奇心旺盛"]
strengths = "思いやりがある"
weaknesses = "やや内向的"

[background]                        # 任意・散文OK
origin = '''幼少期に母親を病気で亡くし、医療文学を志す。'''

[[relations]]                       # 任意・0件以上
target = "chara-002"                # 必須・存在チェック対象 # 佐藤太郎
kind = "学友"
emotion = "信頼"
note = "第1章で出会う"

[[versions]]                        # 任意・章またぎ変化（属性変更の唯一の記録場所）
from_chapter = 3                    # 必須
to_chapter = 4                      # 任意
age = 20                            # 変更されるキーのみ書く
affiliation = "魔法公安"
note = "覚醒後。制服が黒い戦闘服に"
```

**規則**：
- `[[versions]]` に書かれたキーは、その章範囲でルートの値を上書きする
- `[basic]` 配下のキー（`age` / `gender` / `first_person` / `speech_style` / `height_cm`）を versions で書いた場合、pack.py は `[basic]` の対応するキーに反映して出力する（例：`versions.age = 19` → 出力上は `basic.age = 19` として解決）
- versions 同士の章範囲が重複したら validate エラー
- `age` などキャラ固有の追加キーは自由（スキーマは必須キーのみ検証）

---

## 2. worldbuilding（worldbuilding/world-NNN.toml）

```toml
id = "world-001"
title = "世界観基本設定"
kind = "core"                       # core / geography / rules / glossary 等

content = '''魔法が科学と共存する現代日本。魔法は「術式」として体系化され、国家資格制度がある。'''

[[constraints]]                     # 任意・制約リスト（時代考証チェック用）
kind = "forbidden_words"            # forbidden_words / unknown_to / era
words = ["スマホ", "SNS", "コンビニ"]
note = "舞台は大正時代のため使用禁止"
target = "chara-003"                # unknown_to の場合のみ・誰の知識範囲外か
```

**規則**：
- 世界観系は `content` の散文 + 構造化可能な部分はテーブル/配列で、の併用を許可
- `[[constraints]]` は pack.py が全件コンテキストへ展開する

---

## 3. plot（plot/plot-chNN.toml）

```toml
id = "plot-ch01"                    # 必須・ファイル名と一致（plot-chNN）
chapter = 1                         # 必須・章番号（整数）
title = "覚醒"                      # 必須
peak_intensity = 60                 # 任意・感情曲線のピーク(%)
pov = "chara-001"                   # 推奨・基本視点キャラ # 桜井美咲

summary = ""                        # 章要約。執筆後にLLMがproposedで記入
summary_status = "proposed"         # summary の確定状態

[[scenes]]                          # 必須・1件以上
title = "大学の廊下"                # 必須
location = "私立大学・1号館3階"      # 必須
time = "午後・雨"                   # 推奨
pov = "chara-001"                   # 必須・章povと異なる場合はこちら優先
characters = ["chara-001", "chara-002"]  # 必須・登場キャラID列
content = '''美咲は窓の外を見ていた。雨粒がガラスを伝い——'''  # 必須・演出指示
emotion_peak = "静かな導入"          # 任意

[[foreshadowing]]                   # 任意・伏線
id = "fs-001"                       # 必須
content = "太郎の机の古びた写真。裏に「M.T. 2018」の走り書き"
resolve_chapter = 3                 # 必須・回収予定章
resolved_at = 3                     # 回収済の場合の実績章。未回収は省略

[[established]]                     # 任意・この章で確定した出来事・関係変化
content = "美咲が魔法適性に覚醒した"
status = "confirmed"                # proposed / confirmed
characters = ["chara-001"]          # 関連キャラ（任意）
```

**規則**：
- 本文は `novel/chNN.md` にのみ書く。`scenes.content` はプロット（演出指示）であり本文の複製にしない
- 伏線の回収は `resolved_at` に一元化。established に伏線回収は書かない
- validate は `resolve_chapter` と `resolved_at` の整合（未回収のまま最終章を超えていないか等）をチェック

---

## 4. meta（meta.toml）

```toml
[work]
title = "作品タイトル"
genre = "現代ファンタジー"
status = "writing"                  # planning / writing / revision / complete

[[chapters]]                        # 必須・章の唯一の目次。記述順が章順
number = 1                          # 必須
plot = "plot/plot-ch01.toml"        # 必須・存在チェック対象
novel = "novel/ch01.md"             # 本文ファイル。未執筆は省略
status = "draft"                    # draft / written / revised / confirmed
```

**規則**：
- 章順はファイル名ではなく本ファイルの `[[chapters]]` 記述順で決まる
- pack.py / validate.py はこの目次を起点に探索する

---

## 5. validate.py 検証項目一覧

| # | 検証 | 重要度 |
|---|------|--------|
| 1 | TOML 構文 | エラー（停止） |
| 2 | 必須キーと型 | エラー |
| 3 | ファイル名 = id の一致 | エラー |
| 4 | ID 重複（プロジェクト全体） | エラー |
| 5 | 参照 ID の存在（relations.target / scenes.characters / pov） | エラー |
| 6 | meta.toml のファイルパス存在 | エラー |
| 7 | versions 章範囲の重複・逆転 | エラー |
| 8 | 伏線 resolve_chapter 存在・resolved_at との整合 | エラー |
| 9 | established / summary の status が proposed のまま | **警告** |
| 10 | novel 本文の禁止語彙（worldbuilding [[constraints]] と照合） | 警告 |
| 11 | 初出キャラのふりがな（本文との照合） | 警告 |
| 12 | 一人称の揺れ（本文 vs character.first_person） | 警告 |

`validate.py --index`：全 ID と name_ja / title の対応一覧を出力。

> **実装状況（v0.3.0）**：1〜9 に加え、`meta.toml chapters[].novel` パス存在チェックと proposal↔character 照合（人物名・ふりがな・警告系）を `scripts/validate.py` に実装済み。10〜12 の本文検査は `scripts/check_prose.py`（新設）が担当する。planning 中（`work.status = "planning"`）の `[[chapters]]` 未記入は警告（許容）。

---

## 6. pack.py 出力仕様

入力：章番号 N。出力：`.context/chNN.md`

### 6.1 収録内容
1. meta.toml から対象章を特定
2. 登場キャラ = 対象章 scenes.characters の和集合 → 各キャラの `from_chapter ≦ N ≦ to_chapter` を満たす version で属性を解決
3. worldbuilding の `[[constraints]]` 全件
4. 前章：`novel/chN-1.md` 全文。それ以前：各章の `summary`（confirmed のみ、未確定は established から代替）
5. 未回収伏線：`resolve_chapter ≦ N` かつ `resolved_at` なし
6. established：N 未満の章の全件。`status = "proposed"` は「【未確定】」を頭に付記

### 6.2 established のロールアップ（長編対策）
30章超で established 全件展開は budget を圧迫するため、次の規則で圧縮する。

- **直近2章分（N-1, N-2）の established は全件そのまま展開**
- **3章以上前（N-3 以前）の established は章単位で1行にロールアップ**（例：「第12章：甲野が離反、乙が負傷」）
- **`status = "proposed"` はロールアップせず全件残す**（未確定事項の取りこぼし防止）

### 6.3 budget 超過時の削り順
`--budget`（既定 100K トークン相当）超過時は、以下の順で削る。上位ほど優先的に残す。

1. 対象章メタデータ・登場キャラ（versions 解決済）— **削らない**
2. worldbuilding 制約
3. 未回収伏線 — **削らない**（§6.5 抽出漏れ禁止のため、budget 制御の対象外）
4. established（proposed 全件 → 6.2 ロールアップ後。章単位の block で落とす）
5. それ以前の章 summary（古い章から順に落とす。章ごと 1 block）
6. 直前章本文（末尾から削る。削りきれない場合は block 丸ごと削除）

> 補足：実装上は「priority 1（対象章＋キャラ）と伏線を固定し、本文 → summary → established → 制約の順で落とす」。budget に全く収まらない場合は priority 1 のみ残す。[OK/NOTE ログ](../scripts/pack.py)に削った内容を明示出力する。

### 6.5b established の budget 粒度
established は「章ごとに集約した 1 block」とする（直近2章分の全件行＋ロールアップ行を 1 block に束ねない。古い章から章単位で落とせる粒度を保つ）。

### 6.4 鮮度チェック（pack 忘れガード）
`pack.py --check`：`character/`・`worldbuilding/`・`plot/`・`novel/` の mtime が対象 `.context/chNN.md` より新しい場合に警告を出す。**`--chapter N` 付きの場合は第 N 章のパックを構成する原典だけを比較する**（対象章とそれ以前の章の plot/novel。後続章の本文更新で前章パックが誤判定されない）。章指定なしの場合は全パック一括。執筆ワークフロー冒頭の固定1手：`validate.py → pack.py --check → 必要なら pack.py → .context/chNN.md を読む`。

### 6.5 テスト要件（P1 受け入れ条件）
pack.py は新構成における唯一の情報源（単一点）のため、以下は実装と同時にテストで担保する。

- versions の重複・逆転の解決が仕様通りであること
- 未回収伏線の抽出漏れがないこと（`resolved_at` 有無の境界）
- budget 制御（6.3 の削り順が守られること）
- established ロールアップで proposed が残ること

---

## 7. serialize 規則（廃止）

vecmemori への fact 化は行わないため serialize 規則は存在しない。LLM に渡す表現は pack.py の Markdown レンダリングに一元化される。
