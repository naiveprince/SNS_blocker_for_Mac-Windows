# SNS Access Blocker for Windows

Windows版です。

## 起動

GitHub Releasesから配布される `SNS-Access-Blocker-Windows.exe` を使ってください。

Pythonが入っているPCでは、`SNS Access Blocker Windows.bat` をダブルクリックして起動することもできます。

## exeを作る

Windows上で `Build Windows EXE.bat` をダブルクリックしてください。

作成後、次の場所にexeができます。

```text
dist\SNS Access Blocker.exe
```

## 確認

```bat
python app.py --self-test
```
