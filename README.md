# car-instagram-automation

Instagram自動投稿基盤。制作工程とは分離し、完成済みメディアを指定日時にMeta公式API経由で投稿する。

## v1 scope

- Instagram Storiesの画像投稿
- 完成済みStory画像 + 投稿日時を入力として扱う
- GitHub Actionsによる定期実行
- 二重投稿防止
- 投稿成功/失敗の状態管理
- エラーログ

## Future

共通基盤を維持したままFeed / Carousel / Reelsを追加できる構造にする。

## Design principle

投稿基盤ではコンテンツを生成しない。画像・動画・キャプション等は制作側で完成させ、投稿基盤は配送のみ担当する。
