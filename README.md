日本語のみ対応しています。

## 主な機能

商品の登録・編集・削除（店員モード）
バーコードスキャンによる商品追加
現金・電子マネー決済
レシート発行（テキストファイル保存）デフォルトの店名は新鮮さかな市場となっております。

使い方

1　admin_barcode.txtに店員バーコードを記入する。
2　起動して店員バーコードをカメラに近づける。
3　商品を登録する（割引しない場合は、0％に設定して下さい）
4　商品をスキャンする。
5　会計方法を選択する。
6　レシートを発行するか選ぶ。


exe版：レシート店名変更機能はv1.0.2のみ利用できます。店員モードの設定で変更できます。

ソースコード版：ソースコード（行： lines.append("====== 新鮮さかな市場 ======")　）を編集すればレシートに記載される店名を変更できます。

推奨Pythonバージョン
3.12


ビルドコマンド（非推奨）

pyinstaller --noconfirm --onefile --windowed --clean --collect-all cv2 --collect-all pyzbar --collect-all PyQt5 セルフレジ風アプリ.py


リンク

お問い合わせフォーム

https://forms.gle/wTKN1Lj9fuA3jFpe9

ホームページ

https://sites.google.com/view/qweryuiopasdfghjklzxcvbnm/%E3%83%9B%E3%83%BC%E3%83%A0

セルフレジ風アプリのホームページ（googleドライブ版はこちらからをダウンロードできます。）

https://sites.google.com/view/ho-mupe-zi/%E3%83%9B%E3%83%BC%E3%83%A0

