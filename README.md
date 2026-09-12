# novel2agent-jp

AI コーディングエージェント（Hermes / Claude Code / opencode / goose 等）で日本語小説を書くためのスキル。

設定を **TOML ファイルに正規化し、Python スクリプトで検証・文脈パック生成する**方式。ベクトルストア等の外部サービスに依存せず、生成物は Markdown なのでどのエージェントでも扱える。

```
TOML ---- validate.py ---- pack.py ---- .context/chNN.md
```

詳細方針は `docs/novel2hermes-jp_アップデート計画_v2.md`、TOML スキーマは `schema/toml-schema.md`。

## インストール

このリポジトリをエージェントのスキルディレクトリに配置する（例: Hermes なら `profiles/<user>/skills/`）。

## 状態

開発中。旧スキル `kgmkm/novel2hermes-jp` の後継。
