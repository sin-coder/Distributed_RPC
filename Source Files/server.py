import os
import sys
import math
import json
import errno
import struct
import signal
import socket
import asyncore
from io import BytesIO
from kazoo.client import KazooClient

class RPCHandler(asyncore.dispatcher_with_send):
	def __init__(self,sock,addr):
		asyncore.dispatcher_with_send.__init__(self,sock = sock)
		self.addr = addr
		self.handlers = {                  #RPC服务函数注册
			"ping": self.ping,
			"pi":self.pi,
			"fibonaqi":self.fibonaqi
		}
		self.rbuf = BytesIO()
	def handle_connect(self):            #重写连接函数
		print(self.addr,"comes")

	def handle_close(self):              #重写关闭连接函数
		print(self.addr,"bye")
		self.close()

	def handle_read(self):               #处理半包问题
		while True:
			content = self.recv(1024)
			if content:
				self.rbuf.write(content)
			if len(content) < 1024:
				break
		self.handle_rpc()

	def handle_rpc(self):
		while True:
			self.rbuf.seek(0)
			length_prefix  = self.rbuf.read(4)
			if len(length_prefix) < 4:
				break
			length, = struct.unpack("I",length_prefix)
			body = self.rbuf.read(length)
			if len(body) < length:
				break
			request = json.loads(body.decode())
			in_ = request['in']                  #收到请求
			params = request['params']
			print(self.addr,in_,params)          
			handler = self.handlers[in_]         #调用函数处理
			handler(params)

			left = self.rbuf.getvalue()[length + 4:]
			self.rbuf = BytesIO()
			self.rbuf.write(left)
		self.rbuf.seek(0,2)

	def ping(self,params):                  #ping服务函数
		self.send_result("pong",params)
          
	def pi(self,n):                          #求圆周率服务函数
		s = 0.0
		for i in range(n+1):
			s += 1.0/(2*i + 1)/(2*i + 1)
		result = math.sqrt(8*s)
		self.send_result("pi_r",result)

	def fibonaqi(self,n):                   #斐波那契数列值服务函数
		result = self.recursive(n)
		self.send_result("fibonaqi",result)

	def recursive(self,n):
		if n <= 1:
			return n
		return self.recursive(n-1)+self.recursive(n-2)


	def send_result(self,out,result):      #将计算后的结果返回
		body = json.dumps({"out":out,"result":result})
		length_prefix = struct.pack("I",len(body))
		self.send(length_prefix)    
		self.send(body.encode())            #编码


class RPCServer(asyncore.dispatcher):

	zk_root = "/demo"              #zookeeper中的目录节点           
	zk_rpc = zk_root + "/rpc"

	def __init__(self,host,port):
		asyncore.dispatcher.__init__(self)
		self.host = host
		self.port = port
		self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
		self.set_reuse_addr()              #重用地址
		self.bind((host,port))
		self.listen(1)

		self.child_pids = []               #存放子进程的pid号       

		if self.prefork(10):               #创建10个子进程 
			self.register_zk()             #注册服务
			self.register_parent_signal()  #预定义信号处理函数
		else:
			self.register_child_signal()  

    
	def prefork(self,n):
		for i in range(n):
			pid = os.fork()                #父子进程会同时返回
			if pid < 0:                    #无法创建进程
				raise                   
			if pid > 0:                    #父进程返回子进程的pid
				self.child_pids.append(pid)
			if pid == 0:                   #子进程
				return False
		return True

    
	def register_zk(self):
		self.zk = KazooClient(hosts = "127.0.0.1:2181")  #连接本地的zookeeper数据库
		self.zk.start()                     #启动会话

		self.zk.ensure_path(self.zk_root)   #递归创建路径              
		value = json.dumps({"host":self.host,"port":self.port})  #序列化数据
		#创建一个临时的顺序节点
		self.zk.create(self.zk_rpc,value.encode(),ephemeral = True,sequence = True)

	def exit_parent(self,sig,frame):
		self.zk.stop()                #进程退出先关闭会话             
		self.close()                  #再关闭套接字

		asyncore.close_all()            

		pids = []

		for pid in self.child_pids:       #杀死子进程
			print("before kill",pid)
			try:
				os.kill(pid,signal.SIGINT)
				pids.append(pid)
			except OSError as ex:
				if ex.args[0] == errno.ECHILD:   
					continue
				raise ex
			print("after kill",pid)

		for pid in pids:
			while True:
				try:
					os.waitpid(pid,0)     #等到子进程结束
					break
				except OSError as ex:
					if ex.args[0] == errno.ECHILD:   
						break                        
					if ex.args[0] == errno.EINTR:
						raise ex                     
			print("wait over",pid)

	def reap_child(self,sig,frame):             #收割子进程
		print("before reap")
		while True:
			try:
				info = os.waitpid(-1,os.WNOHANG)
				break                              
			except OSError as ex:
				if ex.args[0] == errno.ECHILD:
					return 
				if ex.args[0] == errno.EINTR:
					raise ex   
		pid = info[0]
		try:
			self.child_pids.remove(pid)
		except ValueError:
			pass
		print("after reap",pid)

	def register_parent_signal(self):                 #父进程预定义信号处理函数
		signal.signal(signal.SIGINT, self.exit_parent)
		signal.signal(signal.SIGTERM, self.exit_parent)
		signal.signal(signal.SIGCHLD, self.reap_child) 

	def exit_child(self,sig,frame):
		self.close()   
		asyncore.close_all()  
		print("all socket have been closed")

	def register_child_signal(self):                 #子进程预定义信号处理函数
		signal.signal(signal.SIGINT, self.exit_child)
		signal.signal(signal.SIGTERM, self.exit_child)

	def handle_accept(self):                         #获取客户端的连接
		pair = self.accept()  
		if pair is not None:
			sock,addr = pair
			RPCHandler(sock,addr) 

if __name__ == '__main__':
	host = sys.argv[1]      #外部传入的服务地址和端口      
	port = int(sys.argv[2])
	print(host,port)
	RPCServer(host,port)    #构建RPC服务
	asyncore.loop()         #启动事件轮询  