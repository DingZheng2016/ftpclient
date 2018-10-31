import socket
import re
import random
import utils
import time

class MyFTP():
    def __init__(self):
        self.pasv = True
        self.size = 8192
        self.ip = ''
        self.port = 0
        self.connected = False
        self.q_info = None
        self.q_dir2 = None
        self.pipe = None

    def connect(self, ip='127.0.0.1', port=21):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.settimeout(2)
            self.sock.connect((ip, port))
            self.sock.settimeout(None)
        except Exception:
            if self.pipe:
                self.pipe.send('error')
            return 'connection error.'
        res = self.__recv()
        if res.startswith('220'):
            self.connected = True
            if self.pipe:
                self.pipe.send('connected')
        else:
            if self.pipe:
                self.pipe.send('error')
        return res

    def login(self, username='anonymous', password=''):
        if self.q_info:
            self.q_info.put(utils.colorful('USER ' + username, 'purple'))
        self.sock.send(('USER ' + username + '\r\n').encode())
        res = self.__recv()
        if res.startswith('331'):
            if self.q_info:
                self.q_info.put(utils.colorful('PASS ' + password, 'purple'))
            self.sock.send(('PASS ' + password + '\r\n').encode())
            res = self.__recv()
        return res

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
        res = self.__send_list()
        return res

    def cwd(self, dir):
        self.__send_cwd(dir)

    def pwd(self):
        self.__send_pwd()

    def mkd(self, dir):
        self.__send_mkd(dir)

    def rmd(self, dir):
        self.__send_rmd(dir)

    def rename(self, name_old, name_new):
        self.__send_rnfr(name_old)
        self.__send_rnto(name_new)

    def quit(self):
        self.sock.close()
        self.connected = False

    def __recv(self):
        s = ''
        while True:
            res = self.sock.recv(self.size).decode()
            s = s + res
            sp = s.split('\n')
            end = False
            for row in sp:
                if re.match('[0-9]{3} .*', row):
                    end = True
                    break
            if end:
                break
        s.strip('\r\n')
        if self.q_info:
            self.q_info.put(utils.readable(s))
        return s

    def __send_type(self, t='I'):
        if self.q_info:
            self.q_info.put(utils.colorful('TYPE ' + t, 'purple'))
        self.sock.send(('TYPE ' + t + '\r\n').encode())
        self.__recv()

    def __send_pasv(self):
        if self.q_info:
            self.q_info.put(utils.colorful('PASV', 'purple'))
        self.sock.send(('PASV' + '\r\n').encode())
        res = self.__recv()
        if res.startswith('227 '):
            raw = re.search('([0-9]{1,3},){5}[0-9]{1,3}', res)
            raw = raw.group(0)
            numl = raw.split(',')
            self.ip = '.'.join(numl[:4])
            self.port = int(numl[4]) * 256 + int(numl[5])

    def __send_port(self):
        self.ip = '127.0.0.1'
        self.port = random.randint(20000, 65536)
        portstring = ','.join(self.ip.split('.')) + ',' + str(self.port // 256) + ',' + str(self.port % 256)

        if self.q_info:
            self.q_info.put(utils.colorful('PORT ' + portstring, 'purple'))
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
        if self.q_info:
            self.q_info(utils.colorful('LIST', 'purple'))
        self.sock.send(('LIST' + '\r\n').encode())
        self.sockf = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.pasv:
            self.sockf.connect((self.ip, self.port))
            res = self.__recv()
            dirinfo = ''
            while True:
                res = self.sockf.recv(self.size).decode()
                if not res:
                    break
                dirinfo = dirinfo + res
            print(dirinfo, end='')
        else:
            self.sockf.bind(('0.0.0.0', self.port))
            self.sockf.listen(1)
            res = self.__recv()
            conn, addr = self.sockf.accept()
            with conn:
                while True:
                    res = conn.recv(self.size)
                    if not res:
                        break
                    print(res, end='')

        res = self.__recv()
        self.sockf.close()
        return res

    def __send_mkd(self, dirname):
        self.sock.send(('MKD ' + dirname + '\r\n').encode())
        self.__recv()

    def __send_cwd(self, dirname):
        self.sock.send(('CWD ' + dirname + '\r\n').encode())
        self.__recv()

    def __send_pwd(self):
        self.sock.send(('PWD' + '\r\n').encode())
        self.__recv()

    def __send_rmd(self, dirname):
        self.sock.send(('RMD ' + dirname + '\r\n').encode())
        self.__recv()

    def __send_rnfr(self, name_old):
        self.sock.send(('RNFR ' + name_old + '\r\n').encode())
        self.__recv()

    def __send_rnto(self, name_new):
        self.sock.send(('RNTO ' + name_new + '\r\n').encode())
        self.__recv()

    def run(self, q, q_info, q_dir2, pipe):
        self.q_info = q_info
        self.q_dir2 = q_dir2
        self.pipe = pipe
        while True:
            if not q.empty():
                cmd = q.get()
                if cmd == 'connect':
                    ip = q.get()
                    port = q.get()
                    self.connect(ip, port)
                elif cmd == 'login':
                    username = q.get()
                    password = q.get()
                    self.login(username, password)
                elif cmd == 'exit':
                    break
            else:
                time.sleep(0.000005)

    # just for debug
    def sendcmd(self, command):
        self.sock.send((command + '\r\n').encode())
        self.__recv()
