# SNS Access Blocker

SNSや動画サイトを、指定した時間だけ開けなくするデスクトップアプリです。

例えば「X / Twitterを1時間ブロック」と設定すると、その時間が終わるまでブラウザからアクセスしにくくなります。

このアプリは自己管理や集中支援を目的としています。強力なペアレンタルコントロールや、企業向けのフィルタリング製品ではありません。

## ダウンロード

下のボタンから、自分のパソコンに合うものを選んでください。

[Mac版をダウンロード](https://github.com/naiveprince/SNS_blocker_for_Mac-Windows/releases/latest/download/SNS-Access-Blocker-macOS.zip)

[Windows版をダウンロード](https://github.com/naiveprince/SNS_blocker_for_Mac-Windows/releases/latest/download/SNS-Access-Blocker-Windows.exe)

注: ダウンロードリンクは GitHub Releases に配布ファイルが公開された後に有効になります。リンクが開けない場合は、まだ Release が作成されていない可能性があります。

GitHub Releases から exe / app ファイルをダウンロードして、そのまま使用できます。

ただし、配布済みバイナリの実行に不安がある場合は、ソースコードを確認し、ご自身でビルドしてください。本リポジトリには GitHub Actions のビルド設定が含まれているため、fork したリポジトリ上で同じ手順により実行ファイルを生成できます。

また、実行ファイルを使わずに Python ソースコードを直接実行することもできます。

注: 現在の配布ファイルはコード署名および Notarization を行っていません。そのため、macOS や Windows で起動時に警告が表示される場合があります。

## 使い方

1. アプリを開きます。
2. ブロックしたいサービスを選びます。
3. ブロックする時間を「分」で入力します。
4. `ブロック開始` をクリックします。
5. パソコンの確認画面が出たら許可します。

時間が終わると、自動でブロックは解除されます。

## セキュリティとプライバシーについて

このリポジトリでは、ソースコード、GitHub Actions のビルド設定、[PRIVACY.md](PRIVACY.md)、[SECURITY.md](SECURITY.md) を公開し、アプリの動作を確認できるようにしています。

このアプリが行うこと:

- 選択した SNS / 動画サイトを一時的にブロックします。
- OS の hosts ファイルを一時的に編集します。
- ブロック設定の反映や解除のため、DNS キャッシュを更新 / フラッシュする場合があります。
- Windows では、自動解除のために一度限りのタスクと解除用スクリプトを作成する場合があります。
- ブロック状態の表示のため、ユーザーのホームフォルダに `.sns_access_blocker_state.json` を作成 / 削除する場合があります。このファイルはローカルに保存され、外部へ送信されません。

このアプリが行わないこと:

- 個人情報の収集、保存、送信、共有。
- 利用状況の送信。
- ブラウザ履歴の取得。
- Cookie、パスワード、メッセージ、写真、連絡先、ドキュメントの取得。
- ブラウザ拡張のインストール。
- 外部サーバーとの通信。
- 管理者権限を使って、hosts ファイル、DNS キャッシュ、一時的な解除用スクリプト / タスク以外を意図的に変更すること。

## なぜ管理者権限が必要なのか

このアプリは OS の hosts ファイルを使って、指定したドメイン名を開きにくくします。hosts ファイルの編集には、macOS / Windows ともに管理者権限が必要です。

管理者権限は、次の目的にのみ使います。

- hosts ファイルへのブロック設定の追加。
- タイマー終了時、または `緊急解除` 実行時のブロック設定の削除。
- DNS キャッシュのフラッシュ。
- Windows での一度限りの自動解除タスクと解除用スクリプトの登録 / 削除。

## 配布ファイルについて

GitHub Releases で配布している macOS 版 zip と Windows 版 exe は、`.github/workflows/release.yml` の GitHub Actions workflow で作成されます。タグを push すると、macOS 上で app 入り zip、Windows 上で exe がビルドされ、Release にアップロードされます。

現在は macOS の Developer ID 署名・Notarization、Windows のコード署名は行っていません。OS の警告が表示された場合は、表示内容を確認したうえで実行してください。署名されていない実行ファイルが不安な場合は、ソースコードを確認し、ソースから実行するか、ご自身の fork / 環境でビルドしてください。

## 自分でビルド / 実行する方法

Python が入っている環境では、実行ファイルを使わずにソースコードから起動できます。

macOS:

```sh
cd macOS
python3 app.py
```

Windows:

```bat
cd Windows
python app.py
```

動作確認用のセルフテスト:

```sh
cd macOS
python3 app.py --self-test
```

```bat
cd Windows
python app.py --self-test
```

GitHub Actions で配布ファイルを作る場合は、このリポジトリを fork し、タグを push してください。

```sh
git tag v1.0.0
git push origin v1.0.0
```

ローカルで Windows exe を作る場合は、Windows 上で `Windows/Build Windows EXE.bat` を実行してください。macOS 版 app 入り zip は、GitHub Actions の macOS runner で作成する想定です。

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

## 注意事項

- 管理者権限を持つユーザーは、自分で設定を戻すことができます。
- VPN、プロキシ、別の端末、独自 DNS、ブラウザやアプリ内通信などで回避できる場合があります。
- パソコンがスリープしている間は、解除のタイミングが遅れる場合があります。
- 期限後もアクセスできない場合は、アプリの `緊急解除` を押してください。
- このアプリの目的は自己管理・集中支援です。子どもや従業員の利用を強制的に制限する用途には向いていません。

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
