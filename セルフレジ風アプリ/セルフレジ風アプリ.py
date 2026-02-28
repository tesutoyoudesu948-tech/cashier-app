import sys, random, datetime, cv2, time, winsound
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from pyzbar.pyzbar import decode

PRODUCT_FILE = "products.txt"
ADMIN_BARCODE_FILE = "admin_barcode.txt"
QR_CODE_PATH = "qrcode_sites.google.com.png"

# -------------------------------
# 店員バーコード
# -------------------------------
try:
    with open(ADMIN_BARCODE_FILE, "r", encoding="utf-8") as f:
        ADMIN_BARCODE = f.read().strip()
except:
    ADMIN_BARCODE = "1234567890123"

# -------------------------------
# 商品データ管理
# -------------------------------
def load_products():
    products = {}
    try:
        with open(PRODUCT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "," in line:
                    parts = line.strip().split(",")
                    code, name, price = parts[0], parts[1], int(parts[2])
                    discount = int(parts[3]) if len(parts) > 3 else 0
                    products[code] = {"name": name, "price": price, "discount": discount}
    except:
        pass
    return products

def save_all_products(products):
    try:
        with open(PRODUCT_FILE, "w", encoding="utf-8") as f:
            for code, item in products.items():
                f.write(f"{code},{item['name']},{item['price']},{item.get('discount',0)}\n")
    except:
        print("商品の保存に失敗")

def save_product(code, name, price, discount=0):
    products = load_products()
    products[code] = {"name": name, "price": price, "discount": discount}
    save_all_products(products)

# -------------------------------
# 共通ダイアログ
# -------------------------------
class AppDialog(QDialog):
    def __init__(self, message, parent=None, auto_close_ms=500):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setStyleSheet("""
        QDialog { background-color: rgba(0,0,0,180); }
        QWidget#panel { background-color: #1c1c1c; border-radius: 30px; }
        QLabel { font-size: 35px; color: white; }
        """)

        main = QVBoxLayout()
        panel = QWidget()
        panel.setObjectName("panel")
        layout = QVBoxLayout()

        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)

        layout.addWidget(label)
        panel.setLayout(layout)

        main.addStretch()
        main.addWidget(panel)
        main.addStretch()

        self.setLayout(main)
        self.showFullScreen()

        # 0.5秒後に自動で閉じる
        QTimer.singleShot(auto_close_ms, self.accept)
# -------------------------------
# レシート確認ダイアログ
# -------------------------------
class ReceiptConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.result = False
        self.setStyleSheet("""
        QDialog { background-color: rgba(0,0,0,180); }
        QWidget#panel { background-color: #1c1c1c; border-radius: 30px; }
        QLabel { font-size: 35px; color: white; }
        QPushButton { font-size: 30px; background-color: #0078ff; color: white; padding: 15px; border-radius: 15px; }
        QPushButton:hover { background-color: #3399ff; }
        """)
        main = QVBoxLayout()
        panel = QWidget()
        panel.setObjectName("panel")
        layout = QVBoxLayout()
        label = QLabel("レシートを発行しますか？")
        label.setAlignment(Qt.AlignCenter)
        yes_btn = QPushButton("はい")
        no_btn = QPushButton("いいえ")
        yes_btn.clicked.connect(self.yes)
        no_btn.clicked.connect(self.no)
        layout.addWidget(label)
        layout.addWidget(yes_btn)
        layout.addWidget(no_btn)
        panel.setLayout(layout)
        main.addStretch()
        main.addWidget(panel)
        main.addStretch()
        self.setLayout(main)
        self.showFullScreen()

    def yes(self):
        self.result = True
        self.accept()
    
    def no(self):
        self.result = False
        self.accept()

# -------------------------------
# 支払い方法選択
# -------------------------------
class PaymentMethodDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.method = None
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setStyleSheet("""
        QDialog { background-color: rgba(0,0,0,180); }
        QWidget#panel { background-color: #1c1c1c; border-radius: 30px; }
        QPushButton { font-size: 40px; color:white; background-color:#0078ff; border-radius:20px; padding:20px; }
        QPushButton:hover { background-color:#3399ff; }
        QLabel { font-size: 40px; color: white; }
        """)
        layout = QVBoxLayout()
        panel = QWidget()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout()
        label = QLabel("支払い方法を選択してください")
        label.setAlignment(Qt.AlignCenter)
        panel_layout.addWidget(label)
        cash_btn = QPushButton("現金")
        emoney_btn = QPushButton("電子マネー")
        cash_btn.clicked.connect(lambda: self.select_method("現金"))
        emoney_btn.clicked.connect(lambda: self.select_method("電子マネー"))
        panel_layout.addWidget(cash_btn)
        panel_layout.addWidget(emoney_btn)
        panel.setLayout(panel_layout)
        layout.addStretch()
        layout.addWidget(panel)
        layout.addStretch()
        self.setLayout(layout)
        self.showFullScreen()

    def select_method(self, method):
        self.method = method
        self.accept()

# -------------------------------
# 現金決済ウィンドウ
# -------------------------------
class PaymentWindow(QWidget):
    def __init__(self,total,main_window):
        super().__init__()
        self.total=total
        self.inserted=0
        self.main_window=main_window
        self.setWindowTitle("会計中（現金）")
        self.setStyleSheet("""
        QWidget { background-color: #1c1c1c; color: white; font-family:'Meiryo'; font-size:32px; }
        QLabel { font-size:48px; }
        """)
        layout=QVBoxLayout()
        self.label_total=QLabel(f"合計金額: {self.total} 円")
        layout.addWidget(self.label_total)
        self.label_inserted=QLabel(f"投入金額: {self.inserted} 円")
        layout.addWidget(self.label_inserted)
        self.label_change=QLabel(f"おつり: 0 円")
        layout.addWidget(self.label_change)
        self.setLayout(layout)
        self.timer=QTimer()
        self.timer.timeout.connect(self.auto_insert)
        self.timer.start(500)

    def auto_insert(self):
        coins=[10,50,100,500,1000]
        coin=random.choice(coins)
        self.inserted+=coin
        self.label_inserted.setText(f"投入金額: {self.inserted} 円")
        change=max(0,self.inserted-self.total)
        self.label_change.setText(f"おつり: {change} 円")
        if self.inserted>=self.total:
            self.timer.stop()
            winsound.Beep(1000,200)
            self.finish()

    def finish(self):
        dialog = ReceiptConfirmDialog(self)
        if dialog.exec_() and dialog.result:
            self.print_receipt()
        AppDialog("会計完了！", self).exec_()
        self.main_window.__init__()
        self.main_window.showFullScreen()
        self.close()

    def print_receipt(self):
        lines=[]
        now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append("====== 新鮮さかな市場 ======")
        lines.append(f"日時: {now}")
        lines.append("----------------------")
        for code,count in self.main_window.item_counts.items():
            item=self.main_window.products[code]
            price_with_discount = item["price"]*(100-item.get("discount",0))//100
            lines.append(f"{item['name']} x{count} {price_with_discount*count}円")
        lines.append("----------------------")
        lines.append(f"合計: {self.total}円")
        lines.append(f"投入: {self.inserted}円")
        lines.append(f"おつり: {max(0,self.inserted-self.total)}円")
        lines.append("----------------------")
        lines.append("ありがとうございました。またお越しください")
        filename=f"receipt_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename,"w",encoding="utf-8") as f:
            f.write("\n".join(lines))

# -------------------------------
# 電子マネー決済ウィンドウ
# -------------------------------
class EMoneyWindow(QWidget):
    def __init__(self,total,main_window):
        super().__init__()
        self.total=total
        self.main_window=main_window
        self.setWindowTitle("会計中（電子マネー）")
        self.setStyleSheet("""
        QWidget { background-color: #1c1c1c; color:white; font-family:'Meiryo'; font-size:32px; }
        QLabel { font-size:48px; color:white; }
        """)
        layout=QVBoxLayout()
        label = QLabel("スマホをかざしてください")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.qr_label = QLabel()
        layout.addWidget(self.qr_label)
        pixmap = QPixmap(QR_CODE_PATH).scaled(400,400,Qt.KeepAspectRatio)
        self.qr_label.setPixmap(pixmap)
        self.setLayout(layout)
        self.timer=QTimer()
        self.timer.timeout.connect(self.finish_payment)
        self.timer.setSingleShot(True)
        self.timer.start(5000)

    def finish_payment(self):
        winsound.Beep(1000,200)
        dialog = ReceiptConfirmDialog(self)
        if dialog.exec_() and dialog.result:
            self.print_receipt()
        AppDialog("電子マネー支払い完了！", self).exec_()
        self.main_window.__init__()
        self.main_window.showFullScreen()
        self.close()

    def print_receipt(self):
        lines=[]
        now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append("====== 新鮮さかな市場 ======")
        lines.append(f"日時: {now}")
        lines.append("----------------------")
        for code,count in self.main_window.item_counts.items():
            item=self.main_window.products[code]
            price_with_discount = item["price"]*(100-item.get("discount",0))//100
            lines.append(f"{item['name']} x{count} {price_with_discount*count}円")
        lines.append("----------------------")
        lines.append(f"合計: {self.total}円")
        lines.append("----------------------")
        lines.append("ありがとうございました。またお越しください")
        filename=f"receipt_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename,"w",encoding="utf-8") as f:
            f.write("\n".join(lines))

# -------------------------------
# 店員モード
# -------------------------------
class AdminWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window=main_window
        self.products = load_products()
        self.setWindowTitle("店員モード")
        self.showFullScreen()
        layout=QVBoxLayout()
        title=QLabel("店員モード")
        title.setAlignment(Qt.AlignCenter)
        font=title.font()
        font.setPointSize(32)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        self.product_list=QListWidget()
        self.update_product_list()
        layout.addWidget(self.product_list)

        btn_layout=QHBoxLayout()
        edit_btn=QPushButton("編集/割引")
        delete_btn=QPushButton("削除")
        edit_btn.clicked.connect(self.edit_product)
        delete_btn.clicked.connect(self.delete_product)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)

        self.code_input=QLineEdit(); self.code_input.setPlaceholderText("バーコード")
        self.name_input=QLineEdit(); self.name_input.setPlaceholderText("商品名")
        self.price_input=QLineEdit(); self.price_input.setPlaceholderText("価格")
        self.discount_input=QLineEdit(); self.discount_input.setPlaceholderText("割引(%)")
        add_btn=QPushButton("商品登録")
        add_btn.clicked.connect(self.add_product)
        layout.addWidget(self.code_input)
        layout.addWidget(self.name_input)
        layout.addWidget(self.price_input)
        layout.addWidget(self.discount_input)
        layout.addWidget(add_btn)

        back_btn=QPushButton("通常画面に戻る")
        back_btn.clicked.connect(self.back_to_main)
        layout.addWidget(back_btn)
        self.setLayout(layout)

    def update_product_list(self):
        self.product_list.clear()
        self.products = load_products()
        for code,item in self.products.items():
            self.product_list.addItem(f"{code} | {item['name']} | {item['price']}円 | 割引:{item.get('discount',0)}%")

    def edit_product(self):
        selected=self.product_list.currentItem()
        if not selected: return
        code=selected.text().split(" | ")[0]
        name,ok1=QInputDialog.getText(self,"編集","商品名:",text=self.products[code]['name'])
        if not ok1: return
        price_text,ok2=QInputDialog.getText(self,"編集","価格:",text=str(self.products[code]['price']))
        if not ok2: return
        discount_text,ok3=QInputDialog.getText(self,"編集","割引(%)",text=str(self.products[code].get('discount',0)))
        if not ok3: return
        try:
            price=int(price_text)
            discount=int(discount_text)
        except: AppDialog("価格・割引は数字で入力してください",self).exec_(); return
        self.products[code]={"name":name,"price":price,"discount":discount}
        save_all_products(self.products)
        self.update_product_list()

    def delete_product(self):
        selected=self.product_list.currentItem()
        if not selected: return
        code=selected.text().split(" | ")[0]
        del self.products[code]
        save_all_products(self.products)
        self.update_product_list()

    def add_product(self):
        code=self.code_input.text().strip()
        name=self.name_input.text().strip()
        price_text=self.price_input.text().strip()
        discount_text=self.discount_input.text().strip() or "0"
        if not code or not name or not price_text: return
        try:
            price=int(price_text)
            discount=int(discount_text)
        except: AppDialog("価格・割引は数字で入力してください",self).exec_(); return
        save_product(code,name,price,discount)
        AppDialog("商品を登録しました",self).exec_()
        self.code_input.clear(); self.name_input.clear(); self.price_input.clear(); self.discount_input.clear()
        self.update_product_list()

    def back_to_main(self):
        self.main_window.__init__()
        self.main_window.showFullScreen()
        self.close()

# -------------------------------
# メイン画面
# -------------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.products = load_products()
        self.total = 0
        self.item_counts = {}
        self.setWindowTitle("無人店舗セルフレジ")
        self.showFullScreen()
        self.setStyleSheet("""
        QWidget { background-color: #1c1c1c; color: white; font-family: 'Meiryo'; }
        QLabel#TotalLabel { font-size: 60px; font-weight: bold; color: #00ffcc; }
        QLabel#ItemList { background-color: #2a2a2a; border-radius: 20px; padding: 20px; font-size: 28px; }
        """)
        layout = QVBoxLayout()
        self.total_label = QLabel("合計: 0 円")
        self.total_label.setObjectName("TotalLabel")
        layout.addWidget(self.total_label)
        self.item_list = QLabel("")
        self.item_list.setObjectName("ItemList")
        layout.addWidget(self.item_list)
        self.camera_label = QLabel()
        layout.addWidget(self.camera_label)
        self.checkout_btn = QPushButton("会計")
        self.checkout_btn.setFixedSize(200, 60)
        self.checkout_btn.setStyleSheet("background-color:#ff8800; font-size:28px; color:white; border-radius:15px;")
        self.checkout_btn.clicked.connect(self.checkout)
        layout.addWidget(self.checkout_btn)
        self.setLayout(layout)
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera)
        self.timer.start(40)
        self.last_scanned_times = {}

    def update_camera(self):
        ret, frame = self.cap.read()
        if not ret: return
        codes = decode(frame)
        now = time.time()
        for code in codes:
            barcode = code.data.decode("utf-8").strip()
            if barcode == ADMIN_BARCODE:
                self.cap.release()
                AppDialog("店員認証成功", self).exec_()
                self.admin_window = AdminWindow(self)
                self.admin_window.show()
                self.close()
                return
            last_time = self.last_scanned_times.get(barcode,0)
            if now - last_time > 1:
                self.process_barcode(barcode)
                self.last_scanned_times[barcode] = now
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, rgb.shape[1], rgb.shape[0], QImage.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(qimg))

    def process_barcode(self, code):
        if code in self.products:
            self.add_item_to_cart(code, self.products[code])
        else:
            AppDialog("登録されていない商品です。\n店員をお呼びください", self).exec_()

    def add_item_to_cart(self, code, item):
        price_with_discount = item["price"] * (100 - item.get("discount",0)) // 100
        self.total += price_with_discount
        self.item_counts[code] = self.item_counts.get(code,0)+1
        text = ""
        for c,count in self.item_counts.items():
            p = self.products[c]
            price_with_discount = p["price"] * (100 - p.get("discount",0)) // 100
            text += f"{p['name']} x{count}　{price_with_discount*count} 円\n"
        self.item_list.setText(text)
        self.total_label.setText(f"合計: {self.total} 円")

    def checkout(self):
        if self.total==0:
            AppDialog("商品が選択されていません", self).exec_()
            return
        self.cap.release()
        dialog = PaymentMethodDialog(self)
        if dialog.exec_():
            if dialog.method == "現金":
                self.payment_window = PaymentWindow(self.total,self)
                self.payment_window.showFullScreen()
            else:
                self.emoney_window = EMoneyWindow(self.total,self)
                self.emoney_window.showFullScreen()
            self.close()

# -------------------------------
# 起動
# -------------------------------
if __name__=="__main__":
    app=QApplication(sys.argv)
    win=MainWindow()
    win.show()
    sys.exit(app.exec_())
