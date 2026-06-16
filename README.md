# SNS Access Blocker

SNSや動画サイトを、指定した時間だけ開けなくするデスクトップアプリです。

例えば「X / Twitterを1時間ブロック」と設定すると、その時間が終わるまでブラウザからアクセスしにくくなります。

## ダウンロード

下のボタンから、自分のパソコンに合うものを選んでください。

[Mac版をダウンロード](../../releases/latest/download/SNS-Access-Blocker-macOS.zip)

[Windows版をダウンロード](../../releases/latest/download/SNS-Access-Blocker-Windows.exe)

## 使い方

1. アプリを開きます。
2. ブロックしたいサービスを選びます。
3. ブロックする時間を「分」で入力します。
4. `ブロック開始` をクリックします。
5. パソコンの確認画面が出たら許可します。

時間が終わると、自動でブロックは解除されます。

## Mac版

1. `SNS-Access-Blocker-macOS.zip` をダウンロードします。
2. zipファイルをダブルクリックして展開します。
3. `SNS Access Blocker.app` を開きます。
4. 「開発元を確認できません」と表示された場合は、アプリを右クリックして `開く` を選び、もう一度 `開く` を押してください。

ブロック開始時に、Macの管理者パスワード入力画面が表示されます。

## Windows版

1. `SNS-Access-Blocker-Windows.exe` をダウンロードします。
2. exeファイルをダブルクリックして開きます。
3. Windowsの警告が表示された場合は、内容を確認して `詳細情報`、`実行` の順に押してください。

ブロック開始時に、Windowsのユーザーアカウント制御画面が表示されます。

## 解除したいとき

時間が終わる前に解除したい場合は、アプリを開いて `緊急解除` を押してください。

## 注意

- 管理者権限を持つユーザーは、自分で設定を戻すことができます。
- VPN、プロキシ、別の端末、ブラウザやアプリ独自の通信経路では回避できる場合があります。
- パソコンがスリープしている間は、解除のタイミングが遅れる場合があります。
- 期限後もアクセスできない場合は、アプリの `緊急解除` を押してください。

## 対応サービス

- X / Twitter
- Instagram
- TikTok
- Facebook
- YouTube
- Reddit

追加ドメイン欄に、自分でブロックしたいサイトを追加することもできます。

## 公開者向け

GitHub Releasesに、次の名前でファイルを置くと、このREADMEのダウンロードリンクがそのまま使えます。

- `SNS-Access-Blocker-macOS.zip`
- `SNS-Access-Blocker-Windows.exe`

タグを作ってpushすると、`.github/workflows/release.yml` が自動でMac版app入りzipとWindows版exeを作り、GitHub Releasesへアップロードします。

```sh
git tag v1.0.0
git push origin v1.0.0
```

ローカルで確認する場合:

```sh
cd macOS
python3 app.py --self-test
```
