# GitHub公開手順

この手順は、アプリをGitHubで公開する人向けです。

## 1. GitHubでリポジトリを作る

GitHubで新しいリポジトリを作成してください。

おすすめの名前:

```text
sns-access-blocker
```

公開したい場合は `Public` を選びます。

## 2. このフォルダをGitHubへpushする

ターミナルで次を実行します。

```sh
cd ~/sns-access-blocker
git init
git add README.md PUBLISHING.md .gitignore .github macOS Windows
git commit -m "Initial release"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_NAME/sns-access-blocker.git
git push -u origin main
```

`YOUR_GITHUB_NAME` は自分のGitHubユーザー名に置き換えてください。

## 3. 配布ファイルを自動作成する

タグを作ってpushします。

```sh
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actionsが自動で次のファイルを作ります。

- `SNS-Access-Blocker-macOS.zip`
- `SNS-Access-Blocker-Windows.exe`

作成が終わると、GitHubの `Releases` にアップロードされます。

## 4. READMEのリンクを確認する

GitHubのトップページで、READMEの次のリンクをクリックして確認してください。

- `Mac版をダウンロード`
- `Windows版をダウンロード`

ダウンロードできれば公開準備は完了です。

## 失敗した場合

GitHubの `Actions` タブを開き、赤くなっている実行結果をクリックしてください。

よくある原因:

- タグをpushしていない
- リポジトリのActionsが無効になっている
- GitHub側の一時的なビルド失敗
