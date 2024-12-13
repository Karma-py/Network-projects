import socket
import os
import urllib.parse

HOST = ''
PORT = 5689

def get_content_type(filename):
    if filename.endswith('.html'):
        return 'text/html'
    elif filename.endswith('.css'):
        return 'text/css'
    elif filename.endswith('.png'):
        return 'image/png'
    elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
        return 'image/jpeg'
    elif filename.endswith('.mp4'):
        return 'video/mp4'
    else:
        return 'application/octet-stream'

def receive_request(conn):
    buffer = b''
    while True:
        data = conn.recv(1024)
        if not data:
            break
        buffer += data
        if b'\r\n\r\n' in buffer:
            break
    headers, _, body = buffer.partition(b'\r\n\r\n')
    headers = headers.decode()
    return headers, body

def run_server():
    s = socket.socket()
    s.bind((HOST, PORT))
    s.listen(5)
    print('Server is running...')
    while True:
        conn, addr = s.accept()
        headers, body = receive_request(conn)
        if not headers:
            conn.close()
            continue
        lines = headers.split('\n')
        first_line = lines[0]
        parts = first_line.strip().split()
        if len(parts) >= 3:
            method = parts[0]
            path = parts[1]
            version = parts[2]
        else:
            conn.close()
            continue
        print(f"Got a request from {addr} : {method} {path} {version}")
        if path in ['/', '/en', '/index.html', '/main_en.html']:
            filename = 'main_en.html'
        elif path in ['/ar', '/main_ar.html']:
            filename = 'main_ar.html'
        else:
            filename = path.strip('/')
        if method == 'GET':
            if os.path.isfile(filename):
                content_type = get_content_type(filename)
                with open(filename, 'rb') as f:
                    content = f.read()
                response = f'HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\n\r\n'
                conn.sendall(response.encode() + content)
            else:
                html = (
                    '<html><head><title>Error 404</title></head>'
                    '<body><h1 style="color:red;">The file is not found</h1>'
                    f'<p>Client IP: {addr[0]}</p><p>Client Port: {addr[1]}</p></body></html>'
                )
                response = 'HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n' + html
                conn.sendall(response.encode())
        elif method == 'POST':
            if path == '/request_file':
                content_length = 0
                for line in lines:
                    if line.lower().startswith('content-length:'):
                        content_length = int(line.split(':')[1].strip())
                        break
                while len(body) < content_length:
                    data = conn.recv(1024)
                    if not data:
                        break
                    body += data
                body = body.decode()
                data = urllib.parse.parse_qs(body)
                file_name = data.get('file_name', [''])[0]
                file_type = data.get('file_type', [''])[0]
                if os.path.isfile(file_name):
                    content_type = get_content_type(file_name)
                    with open(file_name, 'rb') as f:
                        content = f.read()
                    response = f'HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\n\r\n'
                    conn.sendall(response.encode() + content)
                else:
                    if file_type == 'image':
                        url = 'https://www.google.com/search?tbm=isch&q=' + urllib.parse.quote(file_name)
                    elif file_type == 'video':
                        url = 'https://www.youtube.com/results?search_query=' + urllib.parse.quote(file_name)
                    else:
                        url = '/'
                    response = f'HTTP/1.1 303 See Other\r\nLocation: {url}\r\n\r\n'
                    conn.sendall(response.encode())
            else:
                response = 'HTTP/1.1 405 Method Not Allowed\r\n\r\n'
                conn.sendall(response.encode())
        else:
            response = 'HTTP/1.1 405 Method Not Allowed\r\n\r\n'
            conn.sendall(response.encode())
        conn.close()

if __name__ == '__main__':
    run_server()
