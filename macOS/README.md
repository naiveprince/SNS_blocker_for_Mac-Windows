# SNS Access Blocker for macOS

macOS版です。

## 起動

`SNS Access Blocker.app` を開いてください。

開けない場合は `SNS Access Blocker.command` をダブルクリックしてください。

このフォルダ内の開発用appはPythonを使って起動します。一般公開用のMac版zipは、GitHub ActionsでPython同梱のappとして作成されます。

## ターミナルで起動

```sh
cd macOS
python3 app.py
```

## 確認

```sh
python3 app.py --self-test
```
