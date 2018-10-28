import socket

class MyFTP():
    def __init__(self):
        pass

    def connect(self, ip='127.0.0.1', port=21):
    	pass

    def login(self, username='anonymous', password=''):
    	pass

    def type(self, type='I'):
    	pass

    def pasv(self):
    	pass

    def port(self, ip, port):
    	pass

    def syst(self):
    	pass

    def retr(self, filename):
    	pass

    def stor(self, filename_remote, filename_local):
    	pass

    def list(self):
    	pass

    def mkd(self, dirname):
    	pass

    def cwd(self, dirname):
    	pass

    def pwd(self):
    	pass

    def rmd(self, dirname):
    	pass

    def rename(self, name_old, name_new):
    	pass

    def quit(self):
    	pass

ftp = MyFTP()
ftp.connect('127.0.0.1', 10006)

