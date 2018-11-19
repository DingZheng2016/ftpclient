import sys
import utils
from client import MyFTP
from PyQt5.QtWidgets import QMainWindow, QPushButton, QApplication, QHBoxLayout, \
	QLabel, QGridLayout, QWidget, QLineEdit, QTextBrowser, QTableWidget, QTableWidgetItem, \
	QProgressBar, QHeaderView, QAction, QMenu, QInputDialog
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QCursor
import multiprocessing
import threading
import time
import subprocess
import re


class FTPClient(QMainWindow):

	sig_info = pyqtSignal(str)
	sig_dir2 = pyqtSignal(str)
	sig_progress = pyqtSignal(dict)

	def __init__(self):
		super().__init__()
		self.title = 'My FTP Client'
		self.left = 200
		self.top = 200
		self.width = 1312
		self.height = 768
		self.initUI()
		self.dir1info = ''

		self.currentDir = '/'
		self.progressNumber = 0
		self.progressDic = {}

		self.ftp = MyFTP()
		self.q_info = multiprocessing.Queue()
		self.q_dir2 = multiprocessing.Queue()
		self.q_cmd = multiprocessing.Queue()
		self.q_progress = multiprocessing.Queue()
		self.parentPipe, self.childPipe = multiprocessing.Pipe()

		self.sig_info.connect(self.renderInfo)
		self.sig_dir2.connect(self.renderDir2)
		self.sig_progress.connect(self.renderProgress)


		self.connected = False
		self.exit = False

		th_info = threading.Thread(target=self.recvInfo)
		th_dir2 = threading.Thread(target=self.recvDir2)
		th_progress = threading.Thread(target=self.updateProgress)
		# th_dir1 = threading.Thread(target=self.updateDir1)
		th_info.start()
		th_dir2.start()
		th_progress.start()
		# th_dir1.start()

		pc_ftp = multiprocessing.Process(target=self.ftp.run, args=(self.q_cmd, self.q_info, self.q_dir2, self.childPipe, self.q_progress))
		pc_ftp.start()

		self.renderDir1()

	def initUI(self):
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)
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
		dir1View = QTableWidget(0, 6)
		dir1View.setHorizontalHeaderLabels(("Name", "Type", "Size", "Last Modified", "Permissions", "Owner/Group"))
		dir1View.setShowGrid(False)
		dir1View.doubleClicked.connect(self.dir1clicked)
		dir1View.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

		dir2View = QTableWidget(0, 6)
		dir2View.setHorizontalHeaderLabels(("Name", "Type", "Size", "Last Modified", "Permissions", "Owner/Group"))
		dir2View.setShowGrid(False)
		dir2View.doubleClicked.connect(self.dir2clicked)
		dir2View.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

		# Dir2 Menu
		dir2View.setContextMenuPolicy(Qt.CustomContextMenu)
		dir2View.customContextMenuRequested.connect(self.showRightMenu)

		rightMenu1 = QMenu(dir2View)
		rmdAction = QAction("Delete", dir2View)
		rmdAction.triggered.connect(self.removedir)
		rnAction = QAction("Rename", dir2View)
		rnAction.triggered.connect(self.rename)
		rightMenu1.addAction(rmdAction)
		rightMenu1.addAction(rnAction)

		rightMenu2 = QMenu(dir2View)
		mkdAction = QAction("New Folder", dir2View)
		mkdAction.triggered.connect(self.makedir)
		rightMenu2.addAction(mkdAction)

		self.rightMenu1 = rightMenu1
		self.rightMenu2 = rightMenu2

		progressView = QTableWidget(0, 6)
		progressView.setHorizontalHeaderLabels(("Filename", "Status", "Size", "Progress", "Speed", "Remaining Time"))
		progressView.setShowGrid(False)
		progressView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

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
		self.dir1View = dir1View
		self.dir2View = dir2View
		self.progressView = progressView

	def connect(self):
		self.ip = str(self.ipInput.text()) if self.ipInput.text() else '127.0.0.1'
		self.port = int(self.portInput.text()) if self.portInput.text() else 21
		self.username = str(self.userInput.text()) if self.userInput.text() else 'anonymous'
		self.password = str(self.passInput.text())

		self.q_info.put(utils.colorful('Connecting to ' + self.ip + ':' + str(self.port) + '...', 'black'))

		self.q_cmd.put('connect')
		self.q_cmd.put(self.ip)
		self.q_cmd.put(self.port)

		if not self.parentPipe.recv() == 'connected':
			self.q_info.put(utils.colorful('connect error.', 'red'))
			return

		self.connected = True

		self.q_info.put(utils.colorful('Log in as ' + self.username, 'black'))

		self.q_cmd.put('login')
		self.q_cmd.put(self.username)
		self.q_cmd.put(self.password)

		self.q_cmd.put('list')

	def disconnect(self):
		if not self.connected:
			return
		self.q_info.put(utils.colorful('Disonnected from ' + self.ip + ':' + str(self.port), 'black'))
		self.q_cmd.put('quit')

	def recvInfo(self):
		while True:
			if not self.q_info.empty():
				info = self.q_info.get()
				self.sig_info.emit(info)
			if self.exit:
				break
			time.sleep(0.000005)

	def recvDir2(self):
		while True:
			if not self.q_dir2.empty():
				info = self.q_dir2.get()
				self.sig_dir2.emit(info)
			if self.exit:
				break
			time.sleep(0.000005)

	def updateProgress(self):
		while True:
			if not self.q_progress.empty():
				dic = self.q_progress.get()
				self.sig_progress.emit(dic)
			if self.exit:
				break
			# time.sleep(0.000005)

	def renderInfo(self, info):
		self.infoView.append(info)

	def renderDir1(self):
		proc = subprocess.Popen(['ls', '-l', self.currentDir], stdout=subprocess.PIPE)
		listinfo = proc.stdout.read().decode()
		if listinfo == self.dir1info:
			return
		self.dir1info = listinfo
		listinfo = listinfo.split('\n')
		while self.dir1View.rowCount() > 0:
			self.dir1View.removeRow(0)

		self.appendDirRow(self.dir1View, ['..', '', '', '', '', ''])
		for row in listinfo:
			row = re.sub(' +', ' ', row)
			cols = row.split(' ')
			if len(cols) < 9:
				continue
			typ = 'File' if cols[0][0] == '-' else 'Directory'
			self.appendDirRow(self.dir1View, [cols[8], typ, cols[4], ' '.join(cols[5:8]), cols[0], '/'.join(cols[2:4])])

	def renderDir2(self, listinfo):
		listinfo = listinfo.split('\n')

		while self.dir2View.rowCount() > 0:
			self.dir2View.removeRow(0)
		self.appendDirRow(self.dir2View, ['..', '', '', '', '', ''])
		for row in listinfo:
			row = re.sub(' +', ' ', row)
			cols = row.split(' ')
			if len(cols) < 9:
				continue
			typ = 'File' if cols[0][0] == '-' else 'Directory'
			self.appendDirRow(self.dir2View, [' '.join(cols[8:]), typ, cols[4], ' '.join(cols[5:8]), cols[0], '/'.join(cols[2:4])])

	def dir1clicked(self, mi):
		row = mi.row()
		col = mi.column()
		if col > 0:
			return
		val = self.dir1View.item(row, col).text()
		typ = self.dir1View.item(row, 1).text()
		if typ == 'File':
			if not self.connected:
				return
			self.q_cmd.put('stor')
			self.q_cmd.put(val)
			self.q_cmd.put(self.currentDir)
			self.progressNumber = self.progressNumber + 1
			self.q_cmd.put(self.progressNumber)
			size = int(self.dir1View.item(row, 2).text())
			self.newProgress(self.progressNumber, val, size, 1)
		else:
			self.currentDir = self.currentDir + val + '/'
			print(self.currentDir)
			self.renderDir1()

	def dir2clicked(self, mi):
		if not self.connected:
			return
		row = mi.row()
		col = mi.column()
		if col > 0:
			return
		val = self.dir2View.item(row, col).text()
		typ = self.dir2View.item(row, 1).text()
		if typ == 'File':
			self.q_cmd.put('retr')
			self.q_cmd.put(val)
			self.q_cmd.put(self.currentDir)
			self.progressNumber = self.progressNumber + 1
			self.q_cmd.put(self.progressNumber)
			size = int(self.dir2View.item(row, 2).text())
			self.newProgress(self.progressNumber, val, size, 0)
		else:
			self.q_cmd.put('cd')
			self.q_cmd.put(val)
			if not self.parentPipe.recv() == 'cwd':
				return
			self.q_cmd.put('list')

	def newProgress(self, number, filename, size, status):
		pos = self.progressView.rowCount()
		self.progressView.insertRow(pos)
		bar = QProgressBar()
		self.progressView.setItem(pos, 0, QTableWidgetItem(filename))
		self.progressView.setItem(pos, 1, QTableWidgetItem("Download" if status == 0 else "Upload"))
		self.progressView.setItem(pos, 2, QTableWidgetItem(str(size)))
		self.progressView.setCellWidget(pos, 3, bar)
		self.progressView.setItem(pos, 4, QTableWidgetItem("0 KB/s"))
		self.progressView.setItem(pos, 5, QTableWidgetItem("-"))
		self.progressDic[number] = bar

	def renderProgress(self, dic):
		pos = dic['no'] - 1
		totalSize = int(self.progressView.item(pos, 2).text())
		remaining = (totalSize - dic['size']) / dic['speed'] / 1000
		self.progressDic[dic['no']].setValue(dic['size'] / totalSize * 100)
		self.progressView.setItem(pos, 4, QTableWidgetItem('%.2f' % dic['speed'] + 'KB/s'))
		self.progressView.setItem(pos, 5, QTableWidgetItem('%.2f' % remaining + 's'))

	def appendDirRow(self, dirView, row):
		pos = dirView.rowCount()
		dirView.insertRow(pos)
		for i in range(6):
			dirView.setItem(pos, i, QTableWidgetItem(row[i]))

	def closeEvent(self, event):
		self.exit = True
		self.q_cmd.put('exit')

	def showRightMenu(self, pos):
		if not self.connected:
			return
		index = self.dir2View.selectionModel().currentIndex()
		row = index.row()
		col = index.column()
		if row >= 1 and col >= 0:
			self.curFilename = self.dir2View.item(row, 0).text()
			self.rightMenu1.exec_(QCursor.pos())
		else:
			self.rightMenu2.exec_(QCursor.pos())

	def removedir(self):
		if not self.connected:
			return
		self.q_cmd.put('rm')
		self.q_cmd.put(self.curFilename)

	def rename(self):
		if not self.connected:
			return
		value, ok = QInputDialog.getText(self, "Rename", "Input new name:", QLineEdit.Normal, "")
		if not ok:
			return
		self.q_cmd.put('rename')
		self.q_cmd.put(self.curFilename)
		self.q_cmd.put(value)

	def makedir(self):
		if not self.connected:
			return
		value, ok = QInputDialog.getText(self, "New Folder", "Input folder name:", QLineEdit.Normal, "")
		if not ok:
			return
		self.q_cmd.put('mkd')
		self.q_cmd.put(value)


if __name__ == "__main__":

	app = QApplication(sys.argv)
	w = FTPClient()
	sys.exit(app.exec_())
