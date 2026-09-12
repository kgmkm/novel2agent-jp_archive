# 執筆ワークフロー（TOML 版）

## 固定手順（冒頭に必ずこの順で回す）

```bash
python scripts/validate.py --project-dir <project>
python scripts/pack.py --project-dir <project> --chapter N --check   # 鮮度チェック
# 古い場合のみ:
python scripts/pack.py --project-dir <project> --chapter N
```

以後、`.context/chNN.md` を読んで執筆する。**キャラ・世界観・伏線・前章の情報はパックのみから得る**。TOML 群の直接読込はしない（pack.py が単一情報源）。

セッション開始時（既存プロジェクトの継ぎ）：

1. AGENTS.md（作品の憲法）を読む
2. proposal.md を読む
3. 上記の固定手順でパックを生成して読む
4. 既存完成原稿があれば 1 本読んで文体のトーンを「正解データ」として採用する。設定の拡張解釈はしない（AGENTS.md にない要素を独自に追加しない）

## 執筆実行

1. 該当章の `.context/chNN.md` に忠実に。シーンごとに `演出:` を確認してから書く
2. **文体： 三人称過去形を基本。キャラの口調・一人称はパックの記載と一貫させる**
3. **五感ローテーション： シーンごとに視覚以外の感覚（聴覚・触覚・嗅覚・味覚）を 2 つ以上**（references/sensory-rotation.md）
4. **比喩： シーンごとに 1〜2 個。クリシェ回避**（references/metaphor-guide.md）
5. 本文は `novel/chNN.md` に保存。plot TOML や .context に本文を書き戻さない
   - **保存直後に必ず確認する**: ファイルが存在し、見出し以外の本文が入っているか（`python scripts/check_prose.py --project-dir <project>`）。LLM の編集経路は本文を空にしたまま見出しと空行だけを保存する事故が実例としてある — 保存後の本文消失に気づかないまま次章へ進まないこと
   - **Markdown 段落は空白なし**: 日本語原稿でも段落頭に全角空白（`\u3000`）を入れない。エージェントの編集経路によって壊れる可能性があるため作品規則とする（check_prose.py が警告する）
6. **執筆中の時代考証**：一文ごとに「時代 / 文化圏 / キャラ知識」の 3 点を意識する。`[[constraints]]` の禁止語彙は最初から使わない（事後修正より執筆時抑制）
7. ユーザが続きを書いたらその直後から再開。意見を求められたら作品クオリティ最大化の方向で提案

## 執筆後の記録更新（TOML への反映）

執筆中に判明した設定・出来事・伏線はすべて TOML に追記する。

| 何か | 書き場所 | status |
|------|---------|--------|
| 属性の変化（年齢・所属・外見） | キャラ TOML の `[[versions]]` | — |
| この章で確定した出来事・関係変化 | 章 TOML の `[[established]]` | 初期値は `proposed`（LLM 提案）→ 推敲完了時に人間が `confirmed` |
| 新たな伏線 | 章 TOML の `[[foreshadowing]]` | `resolve_chapter` は必須。実績は回収時に `resolved_at` |
| 章要約 | 章 TOML の `summary` | `summary_status = "proposed"` で記入 → 人間が confirmed |
| 執筆完了 | meta.toml の該当 `[[chapters]].status` | `draft` → `written` |

LLM が「事実」として自信のない追記は、必ず `status = "proposed"` を付ける。**proposed は validate が警告し、pack は【未確定】付きで次章パックに含める**（黙って省略しない）。

### 追記例

```toml
# plot-ch03.toml に（執筆後に追加）
[[established]]
content = "美咲が旧校舎で魔法に覚醒した"
status = "proposed"
characters = ["chara-001"]

[[foreshadowing]]
id = "fs-003"
content = "覚醒時に美咲が呟いた「203号室」"
resolve_chapter = 5

# meta.toml
# number=3 の status を draft → written
```

追記後は必ず再検証＋パック再生成：

```bash
python scripts/check_prose.py --project-dir <project>   # 本文品質（空本文・禁止語彙・全角空白）
python scripts/validate.py --project-dir <project>
python scripts/pack.py --project-dir <project> --chapter <次の章> 
```

### proposed の確定確認（執筆直後に必ず行う）

要約・established を `proposed` で記入した後、エージェントはユーザに短く確認する:

> 第 N 章の要約と確定事項を記入しました。以下の内容を確定（confirmed）してよいか確認ください:
> - summary: （要約の全文）
> - established: （項目一覧）

**ユーザが明示的に承認した場合だけ**、該当章の `summary_status` と `established[].status` を `confirmed` へ更新する。承認なしに自分で confirmed に変えない。confirm 後は `validate.py` を再実行し、該当章の警告が消えたことを確認する。

## 推敲への引き継ぎ

本文執筆後、references/revision-workflow.md の Phase B（整合性）→ Phase C（読者視点）へ。推敲完了時に proposed → confirmed 変更を忘れないこと。

## 執筆クオリティ基準

| 項目 | 基準 |
|------|------|
| 文体 | 三人称過去形。口調・一人称の一致 |
| 五感 | 視覚以外 2 つ以上/シーン |
| 比喩 | 1〜2 個/シーン。クリシェ回避 |
| 台詞 | キャラの知識状態（Phase A-2 で明記したもの）に合致 |
| 伏線 | 張り→回収が TOML 上で追跡可能（foreshadowing/resolved_at） |
| 時代 | `[[constraints]]` との照合済み |
| 整合性 | 章間の数値・事実が TOML 一貫（pack の established で確認） |
