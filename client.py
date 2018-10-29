import socket
import re
import random

class MyFTP():
    def __init__(self):
        self.pasv = True
        self.size = 8192

    def connect(self, ip='127.0.0.1', port=21):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))
        self.__recv()

    def login(self, username='anonymous', password=''):
        self.sock.send(('USER ' + username + '\r\n').encode())
        res = self.__recv()
        if res.startswith('331'):
            self.sock.send(('PASS ' + password + '\r\n').encode())
            self.__recv()
        else:
            pass

    def set_pasv(self, pasv):
        self.pasv = pasv

    def syst(self):
        self.__send_syst()

    def retrbinary(self, filename):
        self.__send_type()
        if(self.pasv):
            self.__send_pasv()
        else:
            self.__send_port()
        self.__send_retr(filename)

    def storbinary(self, filename):
        self.__send_type()
        if(self.pasv):
            self.__send_pasv()
        else:
            self.__send_port()
        self.__send_stor(filename)

    def retrlines(self):
        self.__send_type()
        if(self.pasv):
            self.__send_pasv()
        else:
            self.__send_port()
        self.__send_list()

    def cwd(self, dir):
        pass

    def pwd(self, dir):
        pass

    def mkd(self, dir):
        pass

    def rmd(self, dir):
        pass

    def rename(self, name_old, name_new):
        pass

    def quit(self):
        pass

    def __recv(self):
        s = ''
        while True:
            res = self.sock.recv(self.size).decode()
            # print(res)
            s = s + res
            sp = s.split('\n')
            end = False
            for row in sp:
                if re.match('[0-9]{3} .*', row):
                    end = True
                    break
            if end:
                break
        print(s, end='')
        return s

    def __send_type(self, t='I'):
        self.sock.send(('TYPE ' + t + '\r\n').encode())
        self.__recv()

    def __send_pasv(self):
        self.sock.send(('PASV' + '\r\n').encode())
        res = self.__recv()
        if res.startswith('227 '):
            raw = re.search('([0-9]{1,3},){5}[0-9]{1,3}', res)
            raw = raw.group(0)
            numl = raw.split(',')
            self.ip = '.'.join(numl[:4])
            self.port = int(numl[4]) * 256 + int(numl[5])
        else:
            print('pasv error')

    def __send_port(self):
        self.ip = '127.0.0.1'
        self.port = random.randint(20000, 65536)
        portstring = ','.join(self.ip.split('.')) + ',' + str(self.port // 256) + ',' + str(self.port % 256)
        self.sock.send(('PORT ' + portstring + '\r\n').encode())
        self.__recv()

    def __send_syst(self):
        self.sock.send(('SYST' + '\r\n').encode())
        self.__recv()

    def __send_retr(self, filename):
        self.sock.send(('RETR ' + filename + '\r\n').encode())
        self.sockf = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.pasv:
            self.sockf.connect((self.ip, self.port))
            res = self.__recv()
            # print(res, end='')
            with open(filename, 'wb') as f:
                while True:
                    res = self.sockf.recv(self.size)
                    if not res:
                        break
                    f.write(res)
        else:
            self.sockf.bind(('0.0.0.0', self.port))
            self.sockf.listen(1)
            res = self.__recv()
            # print(res, end='')
            conn, addr = self.sockf.accept()
            with conn:
                with open(filename, 'wb') as f:
                    while True:
                        res = conn.recv(self.size)
                        if not res:
                            break
                        f.write(res)

        self.__recv()
        self.sockf.close()

    def __send_stor(self, filename):
        self.sock.send(('STOR ' + filename + '\r\n').encode())
        self.sockf = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.pasv:
            self.sockf.connect((self.ip, self.port))
            res = self.__recv()
            # print(res, end='')
            with open(filename, 'rb') as f:
                while True:
                    rep = f.read(self.size)
                    self.sockf.send(rep)
                    if not rep:
                        break
        else:
            self.sockf.bind(('0.0.0.0', self.port))
            self.sockf.listen(1)
            self.__recv()
            conn, addr = self.sockf.accept()
            with conn:
                with open(filename, 'rb') as f:
                    while True:
                        rep = f.read(self.size)
                        conn.send(rep)
                        if not rep:
                            break
    
        self.sockf.close()
        self.__recv()

    def __send_list(self):
        self.sock.send(('LIST' + '\r\n').encode())
        self.__recv()

    def __send_mkd(self, dirname):
        pass

    def __send_cwd(self, dirname):
        pass

    def __send_pwd(self):
        self.sock.send(('PWD' + '\r\n').encode())
        self.__recv()

    def __send_rmd(self, dirname):
        pass

#ftp = MyFTP()
#ftp.connect('127.0.0.1', 10006)

