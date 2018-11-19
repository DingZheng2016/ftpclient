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
        self.q_progress = None

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
            if self.pipe and res.startswith('230'):
                self.pipe.send('ok')
            elif self.pipe:
                self.pipe.send('error')
        else:
            if self.pipe:
                self.pipe.send('error')
        return res

    def set_pasv(self, pasv):
        self.pasv = pasv

    def syst(self):
        res = self.__send_syst()
        return res

    def retrbinary(self, filename, currentDir='./', currentNumber=0):
        self.__send_type()
        if(self.pasv):
            self.__send_pasv()
        else:
            self.__send_port()
        res = self.__send_retr(filename, currentDir, currentNumber)
        return res

    def type(self, t='I'):
        res = self.__send_type(t)
        return res

    def storbinary(self, filename, currentDir='./', currentNumber=0):
        self.__send_type()
        if(self.pasv):
            self.__send_pasv()
        else:
            self.__send_port()
        res = self.__send_stor(filename, currentDir, currentNumber)
        return res

    def retrlines(self):
        self.__send_type()
        if(self.pasv):
            self.__send_pasv()
        else:
            self.__send_port()
        res = self.__send_list()
        return res

    def cwd(self, dir):
        res = self.__send_cwd(dir)
        if self.pipe:
            if res.startswith('250'):
                self.pipe.send('cwd')
            else:
                self.pipe.send('error')
        return res

    def pwd(self):
        res = self.__send_pwd()
        return res

    def mkd(self, dir):
        res = self.__send_mkd(dir)
        return res

    def rmd(self, dir):
        res = self.__send_rmd(dir)
        return res

    def rename(self, name_old, name_new):
        self.__send_rnfr(name_old)
        res = self.__send_rnto(name_new)
        return res

    def quit(self):
        res = self.__send_quit()
        self.sock.close()
        self.connected = False
        return res

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
        res = self.__recv()
        return res

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
        return res

    def __send_port(self):
        self.ip = '127.0.0.1'
        self.port = random.randint(20000, 65536)
        portstring = ','.join(self.ip.split('.')) + ',' + str(self.port // 256) + ',' + str(self.port % 256)

        if self.q_info:
            self.q_info.put(utils.colorful('PORT ' + portstring, 'purple'))
        self.sock.send(('PORT ' + portstring + '\r\n').encode())
        res = self.__recv()
        return res

    def __send_syst(self):
        if self.q_info:
            self.q_info.put(utils.colorful('SYST', 'purple'))
        self.sock.send(('SYST' + '\r\n').encode())
        res = self.__recv()
        return res

    def __send_retr(self, filename, currentDir, currentNumber):
        if self.q_info:
            self.q_info.put(utils.colorful('RETR ' + filename, 'purple'))
        self.sock.send(('RETR ' + filename + '\r\n').encode())
        self.sockf = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.pasv:
            self.sockf.connect((self.ip, self.port))
            res = self.__recv()
            if not res.startswith('150'):
                return
            totalSize = 0
            period = 0
            psize = 0
            with open(currentDir + filename, 'wb') as f:
                while True:
                    start = time.time()
                    res = self.sockf.recv(self.size)
                    if not res:
                        break
                    f.write(res)
                    totalSize += len(res)
                    psize += len(res)
                    end = time.time()
                    period += end - start
                    if period <= 0.2:
                        continue
                    dic = {}
                    dic['no'] = currentNumber
                    dic['speed'] = psize / period / 1024
                    dic['size'] = totalSize
                    if self.q_progress:
                        self.q_progress.put(dic)
                    period = 0
                    psize = 0
                dic = {}
                dic['no'] = currentNumber
                dic['speed'] = psize / period / 1024
                dic['size'] = totalSize
                if self.q_progress:
                    self.q_progress.put(dic)
        else:
            self.sockf.bind(('0.0.0.0', self.port))
            self.sockf.listen(1)
            res = self.__recv()
            if not res.startswith('150'):
                return
            conn, addr = self.sockf.accept()
            totalSize = 0
            period = 0
            psize = 0
            with conn:
                with open(currentDir + filename, 'wb') as f:
                    while True:
                        start = time.time()
                        res = conn.recv(self.size)
                        if not res:
                            break
                        f.write(res)
                        totalSize += len(res)
                        psize += len(res)
                        end = time.time()
                        period += end - start
                        if period <= 0.2:
                            continue

                        dic = {}
                        dic['no'] = currentNumber
                        dic['speed'] = psize / period / 1024
                        dic['size'] = totalSize
                        if self.q_progress:
                            self.q_progress.put(dic)
                        period = 0
                        psize = 0
                    dic = {}
                    dic['no'] = currentNumber
                    dic['speed'] = psize / period / 1024
                    dic['size'] = totalSize
                    if self.q_progress:
                        self.q_progress.put(dic)


        res = self.__recv()
        self.sockf.close()
        return res

    def __send_stor(self, filename, currentDir, currentNumber):
        if self.q_info:
            self.q_info.put(utils.colorful('STOR ' + filename, 'purple'))
        self.sock.send(('STOR ' + filename + '\r\n').encode())
        self.sockf = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.pasv:
            self.sockf.connect((self.ip, self.port))
            res = self.__recv()
            if not res.startswith('150'):
                return
            totalSize = 0
            period = 0
            psize = 0
            with open(currentDir + filename, 'rb') as f:
                while True:
                    start = time.time()
                    rep = f.read(self.size)
                    self.sockf.send(rep)
                    if not rep:
                        break
                    totalSize += len(rep)
                    psize += len(rep)
                    end = time.time()
                    period += end - start
                    if period <= 0.2:
                        continue
                    dic = {}
                    dic['no'] = currentNumber
                    dic['speed'] = psize / period / 1024
                    dic['size'] = totalSize
                    if self.q_progress:
                        self.q_progress.put(dic)
                    period = 0
                    psize = 0
                dic = {}
                dic['no'] = currentNumber
                dic['speed'] = psize / period / 1024
                dic['size'] = totalSize
                if self.q_progress:
                    self.q_progress.put(dic)
        else:
            self.sockf.bind(('0.0.0.0', self.port))
            self.sockf.listen(1)
            self.__recv()
            if not res.startswith('150'):
                return
            conn, addr = self.sockf.accept()
            totalSize = 0
            period = 0
            psize = 0
            with conn:
                with open(currentDir + filename, 'rb') as f:
                    while True:
                        start = time.time()
                        rep = f.read(self.size)
                        conn.send(rep)
                        if not rep:
                            break
                        totalSize += len(rep)
                        psize += len(rep)
                        end = time.time()
                        period += end - start
                        if period <= 0.2:
                            continue
                        dic = {}
                        dic['no'] = currentNumber
                        dic['speed'] = psize / period / 1024
                        dic['size'] = totalSize
                        if self.q_progress:
                            self.q_progress.put(dic)
                        period = 0
                        psize = 0
                    dic = {}
                    dic['no'] = currentNumber
                    dic['speed'] = psize / period / 1024
                    dic['size'] = totalSize
                    if self.q_progress:
                        self.q_progress.put(dic)

        self.sockf.close()
        res = self.__recv()
        return res

    def __send_list(self):
        if self.q_info:
            self.q_info.put(utils.colorful('LIST', 'purple'))
        self.sock.send(('LIST' + '\r\n').encode())
        self.sockf = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.pasv:
            self.sockf.connect((self.ip, self.port))
            res = self.__recv()
            if not res.startswith('150'):
                return
            dirinfo = ''
            while True:
                res = self.sockf.recv(self.size).decode()
                if not res:
                    break
                dirinfo = dirinfo + res
        else:
            self.sockf.bind(('0.0.0.0', self.port))
            self.sockf.listen(1)
            res = self.__recv()
            if not res.startswith('150'):
                return
            conn, addr = self.sockf.accept()
            dirinfo = ''
            with conn:
                while True:
                    res = conn.recv(self.size)
                    if not res:
                        break
                    dirinfo = dirinfo + res
        if self.q_dir2:
            self.q_dir2.put(dirinfo)

        res = self.__recv()
        self.sockf.close()
        return res

    def __send_mkd(self, dirname):
        if self.q_info:
            self.q_info.put(utils.colorful('MKD ' + dirname, 'purple'))
        self.sock.send(('MKD ' + dirname + '\r\n').encode())
        res = self.__recv()
        return res

    def __send_cwd(self, dirname):
        if self.q_info:
            self.q_info.put(utils.colorful('CWD ' + dirname, 'purple'))
        self.sock.send(('CWD ' + dirname + '\r\n').encode())
        res = self.__recv()
        return res

    def __send_pwd(self):
        if self.q_info:
            self.q_info.put(utils.colorful('PWD', 'purple'))
        self.sock.send(('PWD' + '\r\n').encode())
        res = self.__recv()
        return res

    def __send_rmd(self, dirname):
        if self.q_info:
            self.q_info.put(utils.colorful('RMD ' + dirname, 'purple'))
        self.sock.send(('RMD ' + dirname + '\r\n').encode())
        res = self.__recv()
        return res

    def __send_rnfr(self, name_old):
        if self.q_info:
            self.q_info.put(utils.colorful('RNFR ' + name_old, 'purple'))
        self.sock.send(('RNFR ' + name_old + '\r\n').encode())
        res = self.__recv()
        return res

    def __send_rnto(self, name_new):
        if self.q_info:
            self.q_info.put(utils.colorful('RNTO ' + name_new, 'purple'))
        self.sock.send(('RNTO ' + name_new + '\r\n').encode())
        res = self.__recv()
        return res

    def __send_quit(self):
        if self.q_info:
            self.q_info.put(utils.colorful('QUIT', 'purple'))
        self.sock.send(('QUIT' + '\r\n').encode())
        res = self.__recv()
        return res

    def run(self, q, q_info, q_dir2, pipe, q_progress):
        self.q_info = q_info
        self.q_dir2 = q_dir2
        self.pipe = pipe
        self.q_progress = q_progress
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
                elif cmd == 'list':
                    self.retrlines()
                elif cmd == 'cd':
                    d = q.get()
                    self.cwd(d)
                elif cmd == 'retr':
                    d = q.get()
                    currentDir = q.get()
                    currentNumber = q.get()
                    self.retrbinary(d, currentDir, currentNumber)
                elif cmd == 'stor':
                    d = q.get()
                    currentDir = q.get()
                    currentNumber = q.get()
                    self.storbinary(d, currentDir, currentNumber)
                    self.retrlines()
                elif cmd == 'quit':
                    self.quit()
                elif cmd == 'rm':
                    d = q.get()
                    self.rmd(d)
                    self.retrlines()
                elif cmd == 'rename':
                    d1 = q.get()
                    d2 = q.get()
                    self.rename(d1, d2)
                    self.retrlines()
                elif cmd == 'mkd':
                    d = q.get()
                    self.mkd(d)
                    self.retrlines()
                elif cmd == 'exit':
                    break
            else:
                time.sleep(0.000005)

    # just for debug
    def sendcmd(self, command):
        self.sock.send((command + '\r\n').encode())
        self.__recv()
