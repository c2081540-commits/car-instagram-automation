# car-instagram-automation

完成済みInstagramコンテンツをMeta公式APIへ配送する投稿基盤。制作工程とは分離する。

## v1

最初の実装対象は画像/動画Stories。Feed / Carousel / Reelsは将来拡張とし、予約・状態管理とInstagram固有処理を分離する。

### 重要原則

- `data/queue.json` が予約の正本。
- `scheduled_at` の解釈、due判定、期限切れ判定、投稿対象選択は **Pythonだけ** が行う。
- 将来のGASはON/OFF確認と `publish_due.yml` の起動だけを担当し、予約判定を実装しない。
- 手動投稿と予約投稿は同じ `publish.py -> instagram.py` を使う。
- 週次分析とInsight取得は分離する。Insight分析は保存済みデータを読む。

## Files

- `instagram.py` - Meta API接続、Story container作成、公開、Insight取得
- `media_url.py` - repository相対メディアパスをMeta取得用raw URLへ解決
- `post_queue.py` - 予約・due・期限切れ判定の唯一の実装
- `publish.py` - 自動/手動共通の投稿処理
- `data/queue.json` - 予約正本
- `media/stories/YYYY/MM/` - Stories本番メディア

## Queue format

```json
{
  "posts": [
    {
      "content_id": "CAR-STORY-20260815-0800",
      "scheduled_at": "2026-08-15T08:00:00+09:00",
      "status": "pending",
      "retry_count": 0,
      "frames": [
        {
          "order": 1,
          "media": "media/stories/2026/08/2026-08-15_0800_holiday-discount_01.png",
          "media_kind": "IMAGE"
        }
      ]
    }
  ]
}
```

`publish.py` は `frames[].media` を次の形式へ解決してMeta APIへ渡す。

```text
https://raw.githubusercontent.com/{owner}/{repository}/{ref}/{media}
```

既定値はこのpublic repositoryの `main`。必要時は `MEDIA_GITHUB_REPOSITORY` と `MEDIA_GITHUB_REF` で上書きする。

## GitHub configuration

Repository Secrets:

- `INSTAGRAM_USER_ID`
- `INSTAGRAM_ACCESS_TOKEN`

Repository Variables (optional):

- `META_API_VERSION` (default `v24.0`)
- `LATE_GRACE_MINUTES` (default `15`)
- `MEDIA_GITHUB_REPOSITORY`
- `MEDIA_GITHUB_REF`
- `STORY_INSIGHT_METRICS`

Instagram投稿はMeta接続確認と明示的な運用開始後に実行する。
