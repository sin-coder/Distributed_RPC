'''
1.获取服务列表
2.持续监听服务列表的变更，随机选用一个服务器发送ping指令和pi指令
3.当服务列表变更时，需要将新的服务列表和内存中现有的服务列表
进行比对，创建新的连接，关闭旧的连接
'''

import json       
import time        
import struct     
import socket     
import random
from kazoo.client import KazooClient

#全局变量
zk_root = "/demo"
G = {"servers":None}    #远程服务器的对象列表

class RemoteServer(object):  #封装RPC套接字的对象

	def __init__(self, addr):
		self.addr = addr
		self._socket = None

	@property           #在新式类中返回属性值
	def socket(self):   #懒惰连接尝试进行重连
		if not self._socket:
			self.connect()
		return self._socket

	def ping(self,twitter):
		return self.rpc("ping",twitter)

	def pi(self,n):
		return self.rpc("pi",n)

	def fibonaqi(self,n):
		return self.rpc("fibonaqi",n)

	def rpc(self,in_,params):

		sock = self.socket
		request = json.dumps({"in":in_,"params":params})

		length_prefix = struct.pack("I",len(request))

		sock.send(length_prefix)
		sock.sendall(request.encode())
		length_prefix = sock.recv(4)
		length, = struct.unpack("I",length_prefix)
		body = sock.recv(length)
		reponse = json.loads(body)
		return reponse["out"],reponse["result"]

	def connect(self):
		sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		host,port = self.addr.split(":")
		sock.connect((host,int(port)))
		self._socket = sock

	def close(self):
		if self._socket:
			self._socket.close()
			self._socket = None



def init_servers():

	zk = KazooClient(hosts = "192.168.0.211:2181")
	zk.start()

	current_addrs = set()    #当前可用服务地址列表
	def watch_servers(*args):   #闭包函数
		new_addrs = set()
        
		#获取最新的服务地址列表，并持续监听服务地址列表
		for child in zk.get_children(zk_root,watch = watch_servers):
			node = zk.get(zk_root + "/" + child)
			addr = json.loads(node[0])
			new_addrs.add("%s:%d" % (addr["host"],addr["port"]))

		#新增的服务地址列表   最新的减去当前的
		add_addrs = new_addrs - current_addrs

		#删除的服务地址列表
		del_addrs = current_addrs - new_addrs
		del_servers = []

		#先找出所有待删除的server对象
		for addr in del_addrs:
			for s in G["servers"]:
				if s.addr == addr:
					del_servers.append(s)
					break

		#从全局服务地址列表中删除该服务地址
		for server in del_servers:
			G["servers"].remove(server)
			current_addrs.remove(server.addr)

		#将新增的地址添加到当前服务地址列表中
		for addr in add_addrs:
			G["servers"].append(RemoteServer(addr))
			current_addrs.add(addr)

    #首次获取节点列表并持续监听服务列表变更
	for child in zk.get_children(zk_root,watch = watch_servers):
		node = zk.get(zk_root + "/" + child)
		addr = json.loads(node[0])
		current_addrs.add("%s:%d" % (addr["host"],addr["port"]))
	print(current_addrs,type(current_addrs))
	G["servers"] = [RemoteServer(s) for s in current_addrs]
	return G["servers"]


#随机获取一个可用的服务节点
def random_server():    
	if G["servers"] is None:
		init_servers()           #首次需要初始化服务列表 
	if not G["servers"]:         #没有可用对象就直接返回
		return 
	return random.choice(G["servers"])

if __name__ == '__main__':

	for i in range(100):
		#简单的ping测试服务
		server = random_server()       #获取一个当前可用的节点
		if not server:                 
			break                      #如果获取不到就退出
		time.sleep(0.5)              
		try:
			out,result = server.ping("ireader %d" % i)  #这里的server为RemoteServer类的一个实例对象
			print(server.addr,out,result)
		except Exception as ex:
			server.close()             #遇到错误关闭连接
			print(ex)

		#计算圆周率的服务
		server = random_server()
		if not server:
			break
		time.sleep(0.5)

		try:
			out,result = server.pi(i)
			print(server.addr,out,result)
		except Exception as ex:
			server.close()
			print(ex)

		#计算fibonaqi数列的值
		server = random_server()
		if not server:
			break
		time.sleep(0.5)

		try:
			out,result = server.fibonaqi(32)
			print(server.addr,out,result)
		except Exception as ex:
			server.close()
			print(ex)