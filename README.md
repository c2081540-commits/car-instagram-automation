# car-instagram-automation

完成済みInstagramコンテンツをMeta公式APIへ配送する投稿基盤。制作工程とは分離する。

## v1

最初の実装対象は画像/動画Stories。Feed / Carousel / Reelsは将来拡張とし、予約・状態管理とInstagram固有処理を分離する。

### 重要原則

- `data/queue.json` が予約の正本。
- `scheduled_at` の解釈、due判定、期限切れ判定、投稿対象選択は **Pythonだけ** が行う。
- 将来のGASはON/OFF確認と `publish_due.yml` の起動だけを担当し、予約判定を実装しない。
- 手動投稿と予約投稿は同じ `publish.py -> instagram.py` を使う。
- 週次分析とInsight取得は分離する。`insights.py` は取得可能期間内に生データを `data/insights_raw.json` へ蓄積するだけで、分析は別工程が保存済みデータを読む。

## Files

- `instagram.py` - Meta API接続、Story container作成、公開、Insight取得
- `post_queue.py` - 予約・due・期限切れ判定の唯一の実装
- `publish.py` - 自動/手動共通の投稿処理
- `history.py` - Instagram media IDを含む投稿履歴
- `insights.py` - Story Insight生データ回収
- `data/queue.json` - 予約正本
- `data/history.json` - 投稿履歴
- `data/insights_raw.json` - Insightスナップショット

## Queue example

```json
{
  "posts": [
    {
      "content_id": "CAR-STORY-TEST-001",
      "platform": "instagram",
      "media_type": "STORIES",
      "scheduled_at": "2026-08-15T08:00:00+09:00",
      "status": "pending",
      "retry_count": 0,
      "frames": [
        {
          "order": 1,
          "media_kind": "IMAGE",
          "media_url": "https://public.example/story.jpg"
        }
      ]
    }
  ]
}
```

Metaが取得できる公開HTTPS URLを `media_url` に指定する。

## GitHub configuration

Repository Secrets:

- `INSTAGRAM_USER_ID`
- `INSTAGRAM_ACCESS_TOKEN`

Repository Variables (optional):

- `META_API_VERSION` (default `v24.0`)
- `LATE_GRACE_MINUTES` (default `15`)
- `STORY_INSIGHT_METRICS` (実アカウント/APIで確認済みのStory指標だけを設定)

## Initial verification sequence

1. `Meta Connection Check` を手動実行して接続確認。
2. 公開HTTPS URLのテスト画像1枚を `data/queue.json` に `content_id` 付きで登録。
3. `Manual Story Publish` を `content_id` 指定で実行。
4. `data/history.json` に `instagram_media_id` が保存されたことを確認。
5. `Collect Story Insights` を同じ `content_id` で実行。Storyで実際に利用可能なmetricのみ採用し、生レスポンスを保存する。

この段階ではGAS接続・本番予約投入・週次分析は行わない。
