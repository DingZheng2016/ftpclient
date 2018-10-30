import sys
from client import MyFTP
from PyQt5.QtWidgets import QMainWindow, QPushButton, QApplication, QMessageBox, QHBoxLayout, \
	QLabel, QGridLayout, QWidget, QLineEdit, QTextBrowser
import utils


class FTPClient(QMainWindow):
	def __init__(self):
		super().__init__()
		self.title = 'My FTP Client'
		self.left = 200
		self.top = 200
		self.width = 960
		self.height = 513
		self.initUI()

		self.ftp = MyFTP()

	def initUI(self):
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)
		'''
		button = QPushButton('Click me', self)
		button.setToolTip('Thank you for thinking about me')
		button.move(100, 70)
		button.clicked.connect(self.test_method)
		'''
		self.statusBar().showMessage('@Ding Zheng 2018')

		widget = QWidget()


		topLayout = QHBoxLayout()

		ipLabel = QLabel("ip:")
		ipInput = QLineEdit()
		ipInput.setToolTip("default as localhost")
		topLayout.addWidget(ipLabel)
		topLayout.addWidget(ipInput)

		userLabel = QLabel("username:")
		userInput = QLineEdit()
		userInput.setToolTip("default as anonymous")
		topLayout.addWidget(userLabel)
		topLayout.addWidget(userInput)

		passLabel = QLabel("password:")
		passInput = QLineEdit()
		passInput.setEchoMode(QLineEdit.Password)
		topLayout.addWidget(passLabel)
		topLayout.addWidget(passInput)

		portLabel = QLabel("port:")
		portInput = QLineEdit()
		portInput.setToolTip("default as 21")
		topLayout.addWidget(portLabel)
		topLayout.addWidget(portInput)

		connectButton = QPushButton("Connect")
		connectButton.clicked.connect(self.connect)
		topLayout.addWidget(connectButton)

		disconnectButton = QPushButton("Disconnect")
		disconnectButton.clicked.connect(self.disconnect)
		topLayout.addWidget(disconnectButton)

		topLayout.setStretchFactor(ipLabel, 1)
		topLayout.setStretchFactor(ipInput, 16)
		topLayout.setStretchFactor(userLabel, 1)
		topLayout.setStretchFactor(userInput, 12)
		topLayout.setStretchFactor(passLabel, 1)
		topLayout.setStretchFactor(passInput, 12)
		topLayout.setStretchFactor(portLabel, 1)
		topLayout.setStretchFactor(portInput, 1)
		topLayout.setStretchFactor(connectButton, 12)
		topLayout.setStretchFactor(disconnectButton, 8)

		infoView = QTextBrowser()
		dir1View = QTextBrowser()
		dir2View = QTextBrowser()
		progressView = QTextBrowser()

		mainLayout = QGridLayout()
		mainLayout.addLayout(topLayout, 0, 0, 1, 3)
		mainLayout.addWidget(infoView, 1, 0, 1, 4)
		mainLayout.addWidget(dir1View, 2, 0, 1, 2)
		mainLayout.addWidget(dir2View, 2, 2, 1, 2)
		mainLayout.addWidget(progressView, 3, 0, 1, 4)
		mainLayout.setRowStretch(0, 1)
		mainLayout.setRowStretch(1, 4)
		mainLayout.setRowStretch(2, 4)
		mainLayout.setRowStretch(3, 4)
		mainLayout.setColumnStretch(0, 1)
		mainLayout.setColumnStretch(1, 1)
		mainLayout.setColumnStretch(2, 1)
		mainLayout.setColumnStretch(3, 1)

		widget.setLayout(mainLayout)
		self.setCentralWidget(widget)
		self.show()

		self.ipInput = ipInput
		self.portInput = portInput
		self.userInput = userInput
		self.passInput = passInput

		self.infoView = infoView

	def connect(self):
		self.ip = self.ipInput.text() if self.ipInput.text() else '127.0.0.1'
		self.port = int(self.portInput.text()) if self.portInput.text() else 21
		self.username = self.userInput.text() if self.userInput.text() else 'anonymous'
		self.password = self.passInput.text()

		self.infoView.append(utils.colorful('Connecting to ' + self.ip + ':' + str(self.port) + '...', 'black'))

		res = self.ftp.connect(self.ip, self.port).strip('\r\n')
		self.infoView.append(utils.readable(res))

		if not res.startswith('220'):
			return

		self.infoView.append(utils.colorful('Log in as ' + self.username, 'black'))

		res = self.ftp.login(self.username, self.password, self.infoView).strip('\r\n')
		self.infoView.append(utils.readable(res))

		res = self.ftp.retrlines()
		self.infoView.append(utils.readable(res))

	def disconnect(self):
		if not self.ftp.connected:
			return
		self.infoView.append(utils.colorful('Disonnected from ' + self.ip + ':' + str(self.port), 'black'))
		self.ftp.quit()


if __name__ == "__main__":

	app = QApplication(sys.argv)
	w = FTPClient()
	sys.exit(app.exec_())
