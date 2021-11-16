'''
	author: g-tmp
	base on python3/http.server
'''

import os
import io
import sys
import socket
import html
import urllib.parse
import mimetypes
import time
import threading




class File(object):

	def get_filesize(self,file):
		size_unit = ['b','K','M','G','T']
		try:
			size = os.path.getsize(s)
		except OSError as e:
			raise e
		i = 0
		while size/1000 >= 1:
			size = float(size) / 1000
			i += 1

		return '%.1f %s' % (size , size_unit[i])


		# file last modify time
	def get_filemtime(self,file):
		stime = time.localtime(os.path.getmtime(s))
		ftime = time.strftime('%Y-%m-%d %H:%M:%S',stime)

		return ftime




# OK = 200
# NOT_FOUND = 404
# MOVER_PERMANENTLY = 301

class HTTPRequestHandler(object):
	"""
	"""

	def __init__(self):
		self.HOME = os.environ['HOME']
	

	def parse_request(self,request):
		status_line = request.split('\r\n')[0]
		method = status_line.split()[0]
		path = urllib.parse.unquote(status_line.split()[1])

		return (method,path)



	def make_header(self,state_code,path=None,body_length=0):
		server = "XD"
		date = ''

		if state_code == 200:
			if path is None:
				header = 'HTTP/1.1 200 OK\r\nContent-Type: %s\r\nServer: %s\r\n\r\n' % ('text/html',server)
				return header
			
			if os.path.isdir(path)  and  not path.rstrip().endswith('/'):	
				return self.make_header(301,path)

			content_type = self.guess_type(path)
			header = 'HTTP/1.1 200 OK\r\nContent-Type: %s\r\nContent-Length: %d\r\nServer: %s\r\n\r\n' % (content_type,body_length,server)
		elif state_code == 404:
			header = 'HTTP/1.1 404 Not Found\r\nContent-Type: text/html;charset=utf-8\r\nContent-Length: %d\r\nServer: %s\r\nConnection: close\r\n\r\n' % (body_length , server)

		elif state_code == 301:
			if not path.rstrip().endswith('/'):
				location = path + '/'

			header = 'HTTP/1.1 301 Moved Permanently\r\nLocation: %s\r\nServer: %s\r\n\r\n' % (location,server)

		else:
			return None
		
		return header



	def list_directory(self,path):
		'''
			path is REAL path

			path is a file return None
			or 
			path is a diractory list its files and return a fd
		'''

		try:
			lists = os.listdir(path)
		except OSError as e:
			# path is not a diractory
			return None

		os.chdir(path)		# change directory for upload files
		logic_path = path.replace(self.HOME,'')

		r = []
		enc = sys.getfilesystemencoding()
		title = 'Directory listing for %s ' % logic_path
		r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">')
		r.append('<html>\n<head>')
		r.append('<meta http-equiv="Content-Type" content="text/html; charset=%s">' % enc)
		r.append('<title>%s</title>\n</head>' % logic_path)
		r.append('<body>\n<h1>%s</h1>' % title)
		r.append('<form  method="POST" enctype="multipart/form-data">')
		# r.append('<input type="text" name="p1" required="required"> >>')
		r.append('<input type="file"  name="file" > >>')
		r.append('<button type="submit">Upload</button></form>')
		r.append('<hr>\n<ul>')
		try:
			r.append('<a href="%s">Parent Directory</a>' % logic_path[0:logic_path[0:-1].rindex('/')+1])
		except Exception as e:
			r.append('/')


		lists.sort(key=lambda a:a.lower())
		for name in lists:
			fullname = os.path.join(path,name)
			displayname = linkname = name

			if os.path.isdir(fullname):
				displayname = name + "/"
				linkname = name + "/" 
			if os.path.islink(fullname):
				displayname = name + "@"

			r.append('<li><a href="%s">%s</a></li>' % 
				(urllib.parse.quote(linkname,errors='surrogatepass'),  	 # convert the characters in url # , space , ?  to %xx escape
				html.escape(displayname,quote='false') 	)	# Convert the characters &, < and > in string s to HTML-safe sequences.
				)

		r.append('</ul>\n<hr>\n</body>\n</html>\n')
		encode = '\n'.join(r).encode(enc)		# encode WHY?

		# f = io.BytesIO()
		# f.write(encode)
		# f.seek(0)

		return encode	# bytes-like object


	def translate_path(self,path):
		# path = path.split('?',1)[0]
		# path = path.split('#',1)[0]

		real_path = self.HOME + path
		# print('real_path  ',real_path)
		return real_path



	def guess_type(self,path):
		if os.path.isdir(path):
			return "text/html;charset=utf-8"

		content_type = mimetypes.guess_type(path)[0]

		return content_type



	def read_file(self,path):

		buffer = []
		fd = None

		try:
			fd = open(path,'rb')
			# return fd.read()

			while True:
				line = fd.read(4096)
				if not line :
					break

				buffer.append(line)

			buffer = b''.join(buffer)
			return buffer	# byte array

		# no such file
		except IOError as e:	
			raise e
		finally:
			if fd:
				fd.close()


	def do_GET(self,connection_socket,path):
		html = self.list_directory(path)
		response = ''

		if html == None:
			# is a file
			size = os.path.getsize(path)
			outputdata  = self.read_file(path)
			header = self.make_header(200,path,size)
			response = header.encode() + outputdata

		else:
			# is a directory
			header = self.make_header(200,path,len(html))
			response = header.encode() + html
		
		self.send_response(connection_socket,response)



	def do_POST(self,connection_socket,request):
		content_len = int(request.split('Content-Length: ')[1].split('\r\n')[0])
		body = connection_socket.receive_upload(content_len)
		# print("len : "+len(body))
		# print(body)
		connection_socket.upload(body)

		header = self.make_header(200)
		html = '''\
			<TITLE>Upload page for TCP Ethereal Lab</TITLE>
			<body bgcolor="#FFFFFF">
			<p><font face="Arial, Helvetica, sans-serif" size="4"> Congratulations! <br> </font>
			<P><font face="Arial, Helvetica, sans-serif"> You've now transferred a copy of alice.txt from your computer to 
			XD.  You should now stop Wireshark packet capture. It's time to start analyzing the captured Wireshark packets! </font>
			</FORM>
		'''
		response = header.encode('utf-8') + html.encode('utf-8')

		self.send_response(connection_socket,response)


	def send_response(self,connection_socket,response):
		connection_socket.send(response)




class MySocket(object):
	"""
		- coded for clarity, not efficiency
	"""


	def __init__(self, sock = None):
		if sock is None:
			self.__socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
		else:
			self.__socket = sock


	def server_bind(self,host='',port=8000):
		self.__socket.bind((host,port))
		self.__socket.listen(5)
		print("server listening %d <3" % port)


	def server_accept(self):
		return self.__socket.accept()


	def getaddress(self):
		self.__socket.getsockname()


	def send(self,msg):
		# totalsent = 0	
		# while totalsent < MSGLEN:
		# 	sent = self.__socket.send(msg[bytes_sent:])
		# 	if sent == 0:
		# 		raise RuntimeError("socket connection broken")

		# 	bytes_sent += sent 
		return self.__socket.send(msg)




	def receive(self):
		# chunks = []
		# totalrecd = 0	# have received how many bytes
		# while totalrecd < MSGLEN:
		# 	chunk = self.__socket.recv(min(MSGLEN - totalrecd , 2048))
		# 	if chunk == b'':
		# 		raise RuntimeError("socket connection broken")

		# 	chunks.append(chunk)
		# 	totalrecd += len(chunk)

		# return b''.join(chunks)

		return self.__socket.recv(4096)


	def receive_upload(self,msglen):
		chunks = []
		bytes_recvd = 0

		while bytes_recvd < msglen:
			chunk = self.__socket.recv(min(msglen - bytes_recvd, 16 * 1024))
			if chunk == b'':
				raise RuntimeError("socket connection broken")

			bytes_recvd += len(chunk)
			chunks.append(chunk)

		return b''.join(chunks)



	def upload(self,body):
		part = body.split(b"\r\n\r\n")

		part_fields = part[0].split(b"\r\n")

		WebKitFormBoundary = part_fields[0]
		content_disposition = part_fields[1].split(b' ')
		filename = str(part_fields[1].split(b'; ')[-1].split(b'=')[-1].replace(b'"',b'')).replace("'","")
		content_type = part_fields[2].split(b"Content-Type: ")[-1]

		# print(part_fields[1])


		data = part[-1].split(WebKitFormBoundary)[0]
		
		# print(type(filename),filename)

		try:
			with open(filename,'wb') as fd:
				fd.write(data)
		except IOError as e:
			raise e


	def close(self):
		if self.__socket:
			self.__socket.close()

	def shutdown(self):
		self.__socket.shutdown(socket.SHUT_RDWR)




request_handler = HTTPRequestHandler()

def run(connection_socket,addr):
	connection_socket = MySocket(connection_socket)


	try:
		# while True:
		aa = connection_socket.receive();
		# print(aa)
		request = aa.decode('utf-8')
		(method , logic_path ) = request_handler.parse_request(request)
		real_path = request_handler.translate_path(logic_path)
		response = ''
		print(method + "\t" + logic_path)
		# print(request)
		# print(len(request))
			
		if method == "GET":
			request_handler.do_GET(connection_socket,real_path)
		elif method == "POST":
			request_handler.do_POST(connection_socket,request)

	except KeyboardInterrupt as e:
		print("Keyboard Interrupt")
	except IOError as e:
		html = '<br /><font color="red" size="7">404 Not Found!</p>'
		header = request_handler.make_header(404,body_length=len(html))
		response = header.encode() + html.encode()
		connection_socket.send(response)
	finally:
		# print("------- request ------- ")
		# print(request)

		# connection_socket.shutdown()
		connection_socket.close()


		



def start():
	

	welcome_socket = MySocket()
	try:
		port = int(sys.argv[1])
		welcome_socket.server_bind(port=port)
	except IndexError as e:
		welcome_socket.server_bind()

	while True:		
		connection_socket,addr = welcome_socket.server_accept()
		print(addr)
		# connection_socket.settimeout(60)
		t = threading.Thread(target=run , args=(connection_socket,addr))
		t.start()


	welcome_socket.close()



if __name__ == '__main__':
	start()