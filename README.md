主な機能

商品の登録・編集・削除（店員モード）
バーコードスキャンによる商品追加
現金・電子マネー決済
レシート発行（テキストファイル保存）

使い方

1　admin_barcode.txtに店員バーコードを記入する。
2　起動して店員バーコードをカメラに近づける。
3　商品を登録する（割引しない場合は、0％に設定して下さい）
4　商品をスキャンする。
5　会計方法を選択する。
6　レシートを発行するか選ぶ。

ソースコードではレシート発行時の店名を変更できますがexe版では店名変更はできません。
ソースコード版をご利用ください。
推奨Pythonバージョン
3.12

お問い合わせは以下のフォームからお願い致します。

https://forms.gle/wTKN1Lj9fuA3jFpe9


セルフレジ風アプリ 追加機能作成ガイド

このガイドでは、Pythonで作られた「無人店舗セルフレジ」アプリに、誰でも簡単に 追加機能（プラグイン） を作成・適用できる方法を解説します。
追加機能は .txt ファイル形式で用意し、アプリの extensions/ フォルダに置くだけで自動的に読み込まれます。元のアプリの動作やUIは一切壊さず、後から自由に拡張可能です。

1. 追加機能の基本概念

アプリ本体には「拡張フック」がいくつか用意されています。
代表的なものは以下です：

on_add_item(item)

商品がスキャンされてカートに追加された直後に呼ばれるフック

item は辞書型で商品情報を持ちます

{"name": "サーモン", "price": 500, "discount": 10}

将来的に追加できるフック候補

on_checkout_start(total)：会計開始時

on_payment_complete(payment_type)：会計完了時

追加機能はこのフックを使って、商品価格の操作、通知、ログ出力、UI表示などを行うことができます。

2. 追加機能の作成手順
2-1. フォルダ作成

アプリと同じ場所に extensions フォルダを作成します。

mkdir extensions

ここに .txt ファイルを置くと自動的に読み込まれます。

2-2. 追加機能の雛形

基本は以下のようなPythonコードです。

# 例: discount.txt
# 商品スキャン時に10%割引を適用する例

def discount(item):
    # 元の価格から10%割引
    item["price"] = item["price"] * 9 // 10

# アプリに登録
app.on_add_item = discount

ポイント：

関数を作成する

引数はフックの仕様に従う

関数を app.on_add_item に登録する

アプリ本体は登録された関数を呼び出します

2-3. 価格操作の例

商品スキャン時に割引率を変更する例：

def seasonal_discount(item):
    # 商品名が「サーモン」の場合のみ割引
    if "サーモン" in item["name"]:
        item["price"] = item["price"] * 8 // 10  # 20%割引

app.on_add_item = seasonal_discount

これにより、特定の商品だけを割引することが可能です。

2-4. ポップアップ通知の例

商品スキャン時に通知を表示する例：

def notify_item(item):
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtWidgets import QLabel
    # 単純なラベルで通知
    label = QLabel(f"{item['name']} を追加しました！")
    label.setStyleSheet("background-color: yellow; font-size:24px;")
    label.show()
    # 1秒後に自動で閉じる
    QTimer.singleShot(1000, label.close)

app.on_add_item = notify_item

GUI表示も可能

アプリのUIと干渉しないように注意

2-5. ログ出力の例

商品の追加や会計イベントをファイルに記録する例：

def log_item(item):
    with open("scan_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()} - {item['name']} {item['price']}円\n")

app.on_add_item = log_item

ログを残すことで分析や売上管理に活用可能

3. 複数プラグインの読み込み

extensions/ フォルダに複数の .txt を置くと、自動的に順番に読み込まれます。

例えば：

extensions/
├─ discount.txt
├─ log.txt
├─ notify.txt

全ての機能が同時に有効化されます

同じフックを複数登録する場合は、関数内でチェーン処理を行うか、ラップしてまとめます

4. 注意点

Pythonコードで書く

拡張ファイルは .txt ですが、中身はPythonコード

例外処理

try/except を使ってエラーが発生してもアプリが停止しないようにする

GUI操作

フック内でUIを操作する場合は QTimer などで非同期処理を推奨

安全性

拡張コードは任意のPythonを実行できるため、公開時は信頼できるコードのみ使用

5. 高度な拡張アイデア

会計時の特典付与

def cashback(item):
    if item["price"] > 500:
        print(f"{item['name']} はキャッシュバック対象です")
app.on_add_item = cashback

電子マネー支払い専用通知

def emoney_notify(payment_type):
    if payment_type == "電子マネー":
        print("電子マネーで支払い中です")
app.on_payment_complete = emoney_notify

スキャンランキングや売上分析

スキャンごとに商品名を記録

日別ランキングを生成

6. 作成手順まとめ

アプリの extensions/ フォルダを作成

.txt ファイルを作る

フック用の関数を定義

app.on_add_item = 関数名 のように登録

アプリを起動すると自動で読み込まれる

複数プラグインも同様に置くだけで有効

7. まとめ

元のセルフレジの動作はそのまま維持

追加機能は .txt ファイルを置くだけで即座に利用可能

フックシステムで柔軟に拡張可能

Python初心者でも、関数を書いて登録するだけで追加機能が作れる

この仕組みにより、ユーザーは自由に新しい機能を追加したり、割引・通知・ログ・分析などの便利な拡張を簡単に作成できます。
