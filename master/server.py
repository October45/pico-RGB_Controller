import socket
from typing import Tuple, Any
import json
from urllib.parse import unquote


def runServer(port):
    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]

    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('listening on', addr)
    try:
        while True:
            cl, addr = s.accept()
            print('client connected from', addr)
            body = cl.recv(1024)
            body = body.decode('utf-8')
            print(body)
            valid, data = validateRequest(body)
            if valid:
                match data['method']:
                    case 'GET':
                        cl.send(
                            b'HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r')
                        with open('index.html', 'r') as f:
                            cl.send(f.read().encode('utf-8'))
                    case 'POST':
                        print(data['body'])
                        cl.send(
                            b'HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r')
                        response = {
                            'status': 'ok',
                            'data': data['body']
                        }
                        cl.send(
                            b'{' + json.dumps(response).encode('utf-8'))

            cl.shutdown(socket.SHUT_RDWR)
            cl.close()

    except KeyboardInterrupt:
        s.close()
        print('Server stopped')

# Validates the request and parses the data if valid
# Input should be the body as a string or None (Will return False)
# Returns a dictionary of the data and some request information


def validateRequest(body: str | None) -> Tuple[bool, dict | Any]:
    if body == '' or body == None:
        return False
    lines = body.splitlines()
    data = {}
    if lines[0].startswith('GET'):
        data['method'] = 'GET'
        return True, data
    elif lines[0].startswith('POST'):
        data['method'] = 'POST'
    else:
        return False
    lines = lines[1:]
    for line in lines:
        if line == '':
            continue
        elif line.startswith('Content-Type:'):
            data['content-type'] = line.split(' ')[1]
            if data['content-type'].find('form-data') != -1:
                data['boundry'] = '--' + line.split(' ')[2].split('=')[1]
        elif line.startswith('Content-Length:'):
            data['content-length'] = int(line.split(' ')[1])
    if data['method'] == 'POST':
        if 'content-type' not in data or 'content-length' not in data:
            return False
        if data['content-type'].find('form-data') != -1:
            data['content-type'] = 'form-data'
        elif data['content-type'].find('json') != -1:
            data['content-type'] = 'json'
        elif data['content-type'].find('urlencoded') != -1:
            data['content-type'] = 'urlencoded'
        else:
            return False
        if data['content-length'] > 512:
            return False

        if data['content-type'] == 'form-data':
            lines = lines[lines.index(data['boundry']):]
            data['body'] = {}
            for line in lines:
                if line == data['boundry'] or line == data['boundry'] + '--':
                    continue
                elif line.startswith('Content-Disposition: form-data; name="'):
                    key = line.split('"')[1]
                    value = lines[lines.index(line) + 2]
                    data['body'][key] = value
        elif data['content-type'] == 'json':
            lines = lines[lines.index('')+1:]
            data['body'] = json.loads(''.join(lines))
        elif data['content-type'] == 'urlencoded':
            data['body'] = {}
            for value in lines[-1].split('&'):
                key, value = value.split('=')
                data['body'].update({key: unquote(value)})
        if 'boundry' in data:
            del data['boundry']
        return True, data
