import sys
import time
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QMessageBox, QFileDialog
)
from PyQt5.QtCore import QThread, pyqtSignal, QUrl, QObject, pyqtSlot
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel # Yeni Modül

# Renkler
class Colors:
    CYAN = "#00BFFF"
    RED = "#FF6347"
    GREEN = "#7CFC00"
    YELLOW = "#FFD700"
    
# =========================================================================
# ADVANCEDEXPLOITER VE EXPLOITERWORKER sınıfları aynı kalacak
# (Önceki yanıttan kopyalayıp buraya yapıştırabilirsiniz)
# =========================================================================

# Önceki yanıttaki AdvancedExploiter ve ExploiterWorker sınıfları buraya gelecek.
# Yer tutucuları koruyorum:
class AdvancedExploiter:
    def __init__(self, target_url, verbose=False):
        self.target_url = target_url
        self.target_ip = "127.0.0.1" 
        self.open_ports = [80, 443]
        self.vulnerabilities = [{'type': 'Simulated SQLi', 'severity': 'CRITICAL'}]
        self.exploited = [{'type': 'ADVENTR', 'method': 'SUCCESS'}]
    def log(self, message, message_type="INFO"): pass 
    def run_adventr_exploit(self, target_url): self.log("Exploit Çalışıyor...", "EXPLOIT"); time.sleep(4); self.add_exploit("ADVENTR Zafiyeti", "Özel Payload", "Payload başarılı", "Sistem Kök Erişimi Elde Edildi")
    def add_exploit(self, *args): self.exploited.append(args)
    def run_full_penetration_test(self): self.log("Tarama Başlatıldı...", "INFO"); self.run_adventr_exploit(self.target_url)

class ExploiterWorker(QThread):
    update_log = pyqtSignal(str, str)
    scan_finished = pyqtSignal(dict)
    
    def __init__(self, target_url, mode, verbose, parent=None):
        super().__init__(parent)
        self.target_url = target_url
        self.mode = mode
        self.verbose = verbose
    def run(self):
        exploiter = AdvancedExploiter(self.target_url)
        exploiter.log = self._gui_log
        start_time = time.time()
        exploiter.run_full_penetration_test()
        end_time = time.time()
        final_report_data = {
            'target': self.target_url, 'duration': f"{end_time - start_time:.2f} saniye",
            'vulnerabilities': exploiter.vulnerabilities, 'exploits': exploiter.exploited,
            'open_ports': exploiter.open_ports
        }
        self.scan_finished.emit(final_report_data)
    def _gui_log(self, message, message_type="INFO"):
        self.update_log.emit(message, message_type)
        
# =========================================================================

# 1. PYTHON ARKA PLAN SINIFI (JavaScript buradan çağıracak)
class Backend(QObject):
    # Python'dan JavaScript'e log göndermek için sinyal
    log_signal = pyqtSignal(str, str) 
    scan_finished_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.report_data = None
        self.parent_app = parent

    # 🟢 JavaScript'ten çağrılacak metot (Python slotu)
    @pyqtSlot(str, str, bool, result=bool)
    def startScan(self, target_url, mode, verbose):
        if self.worker and self.worker.isRunning():
            self.log_signal.emit("Önceki tarama zaten çalışıyor.", Colors.YELLOW)
            return False

        self.log_signal.emit(f"Python Başlatıldı. Hedef: {target_url}", Colors.CYAN)

        self.worker = ExploiterWorker(target_url, mode, verbose)
        self.worker.update_log.connect(self.log_signal.emit)
        self.worker.scan_finished.connect(self.on_scan_finished)
        self.worker.start()
        return True

    @pyqtSlot(result=bool)
    def saveReport(self):
        return self.parent_app.save_report()

    def on_scan_finished(self, report_data):
        self.report_data = report_data
        # Raporu JSON formatında gönder
        self.scan_finished_signal.emit(report_data)

# --- ANA GUI PENCERESİ Sınıfı ---
class WebEngineApp(QWidget):
    def __init__(self, html_file="gu_v2.html"):
        super().__init__()
        self.setWindowTitle("Advanced Exploiter - Profesyonel HTML GUI")
        self.setGeometry(100, 100, 1200, 800) 
        self.html_file = html_file
        self.report_data = None 
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.web_view = QWebEngineView()
        
        if not os.path.exists(self.html_file):
            QMessageBox.critical(self, "Hata", f"HTML dosyası bulunamadı: {self.html_file}")
            sys.exit(1)

        # 2. QWebChannel Kurulumu
        self.channel = QWebChannel()
        self.backend = Backend(self) # Backend nesnesini oluştur
        self.channel.registerObject('backend', self.backend) # 'backend' adıyla kaydet
        self.web_view.page().setWebChannel(self.channel)
        
        # Log sinyalini JavaScript'e bağla
        self.backend.log_signal.connect(self.log_to_js)
        self.backend.scan_finished_signal.connect(self.on_scan_finished)
        
        file_url = QUrl.fromLocalFile(os.path.abspath(self.html_file))
        self.web_view.load(file_url)
        
        main_layout.addWidget(self.web_view)
        self.setLayout(main_layout)

    def log_to_js(self, message, color):
        # Python logunu JavaScript fonksiyonuna ilet
        self.web_view.page().runJavaScript(f"updateLog('{message}', '{color}')")

    def on_scan_finished(self, report_data):
        self.report_data = report_data
        # JSON verisini stringe çevirip JavaScript'e gönder
        json_string = json.dumps(report_data)
        self.web_view.page().runJavaScript(f"onScanFinished('{json_string}')")

    def save_report(self):
        # Rapor kaydetme mantığı
        if not self.report_data:
            self.backend.log_signal.emit("Rapor verisi bulunamadı.", Colors.YELLOW)
            return False

        filename, _ = QFileDialog.getSaveFileName(
            self, "Raporu Kaydet", 
            f"pentest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
            "JSON Dosyaları (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.report_data, f, indent=4, ensure_ascii=False)
                self.backend.log_signal.emit(f"Rapor kaydedildi: {os.path.basename(filename)}", Colors.GREEN)
                return True
            except Exception as e:
                self.backend.log_signal.emit(f"Kaydetme Hatası: {e}", Colors.RED)
                return False
        return False

# --- Uygulama Başlatma ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = WebEngineApp(html_file="gu_v2.html") 
    ex.show()
    sys.exit(app.exec_())