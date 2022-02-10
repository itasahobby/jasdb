#!/usr/env python3
from __future__ import print_function
from argparse import ArgumentParser
from ctypes import BigEndianStructure,c_uint16
from enum import Enum
import socket

class JasdbMethod(Enum):
    GET = 0, 'GET'
    POST = 1, 'POST'
    UPDATE = 2, 'UPDATE'
    DELETE = 3, 'DELETE'

    def __int__(self):
        return self.value[0]
    
    def __str__(self):
        return self.value[1]

class JasdbHeaderFlags(BigEndianStructure):
    _fields_ = [
        ('METHOD', c_uint16, 2),
        ('ID', c_uint16, 6),
        ('USER', c_uint16, 8),
    ]

class JasdbHeader:
    # Max data size in bytes
    MAX_DATA_SIZE = 510
    MAX_HEADER_SIZE = MAX_DATA_SIZE + 2
    
    def __init__(self, method, id, user, data: bytes):
        self.flags = JasdbHeaderFlags(method, id, user)
        self.data = data[:self.MAX_DATA_SIZE]
    
    def to_bytes(self):
        return bytes(bytearray(self.flags) + self.data)

class Client:
    def __init__(self, address, port, user):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((address, port))
        self.user = user
    def get(self, id):
        payload = JasdbHeader(int(JasdbMethod.GET), id, self.user, b'0')
        socket_data = payload.to_bytes()
        self.socket.send(socket_data)
        response = self.socket.recv(JasdbHeader.MAX_HEADER_SIZE)
        print(response[2:])
    def post(self, data):
        payload = JasdbHeader(int(JasdbMethod.POST), 0, self.user, data)
        socket_data = payload.to_bytes()
        self.socket.send(socket_data)
        response = self.socket.recv(JasdbHeader.MAX_HEADER_SIZE)
        response_flags = JasdbHeaderFlags.from_buffer(bytearray(response[:2]))
        print(response_flags.ID)
    def update(self, id, data):
        payload = JasdbHeader(int(JasdbMethod.UPDATE), id, self.user, data)
        socket_data = payload.to_bytes()
        self.socket.send(socket_data)
        response = self.socket.recv(JasdbHeader.MAX_HEADER_SIZE)
    def delete(self, id):
        payload = JasdbHeader(int(JasdbMethod.DELETE), id, self.user, b'0')
        socket_data = payload.to_bytes()
        self.socket.send(socket_data)
        response = self.socket.recv(JasdbHeader.MAX_HEADER_SIZE)

class Server:
    def __init__(self, address, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((address, port))
        self.database = [0] * (2 ** 6)
    def _handle_request(self, flags, content):
        if flags.METHOD == int(JasdbMethod.GET):
            data = bytes(bytearray(flags) + bytearray(self.database[flags.ID]))
            return data
        elif flags.METHOD == int(JasdbMethod.POST):
            try:
                index = self.database.index(0)
                # If there is free space return the new index
                flags.ID = index
                self.database[index] = content
                data = bytes(bytearray(flags) + bytearray(self.database[flags.ID]))
            except ValueError:
                # No space available
                data = bytes(bytearray(flags) +  b'0')
            return data
        elif flags.METHOD == int(JasdbMethod.UPDATE):
            self.database[flags.ID] = content
            data = bytes(bytearray(flags) + bytearray(self.database[flags.ID]))
            return data
        elif flags.METHOD == int(JasdbMethod.DELETE):
            self.database[flags.ID] = b'0'
            data = bytes(bytearray(flags) + bytearray(self.database[flags.ID]))
            return data

    def run(self):
        self.socket.listen()
        while True:
            conn, _ = self.socket.accept()
            with conn:
                data = conn.recv(JasdbHeader.MAX_HEADER_SIZE)
                if not data: break
                else:
                    flags = JasdbHeaderFlags.from_buffer(bytearray(data[:2]))
                    content = data[2:]
                    payload = self._handle_request(flags, content)
                    conn.send(payload)

if __name__ == '__main__':

    parser = ArgumentParser('jasdb.py')
    subparsers = parser.add_subparsers(required=True, dest='mode')

    parser_server = subparsers.add_parser('server')
    parser_server.add_argument('-a', '--address', default='0.0.0.0')
    parser_server.add_argument('-p', '--port', type=int, default=7001)

    parser_client = subparsers.add_parser('client')
    parser_client.add_argument('-a', '--address', required=True)
    parser_client.add_argument('-p', '--port', type=int, default=7001)
    parser_client.add_argument('-u', '--user', default=0)

    client_method_subparsers = parser_client.add_subparsers(required=True, dest='method')

    parser_client_get = client_method_subparsers.add_parser('get')
    parser_client_get.add_argument('-i', '--id', required=True)

    parser_client_post = client_method_subparsers.add_parser('post')
    parser_client_post.add_argument('-d', '--data', required=True)

    parser_client_update = client_method_subparsers.add_parser('update')
    parser_client_update.add_argument('-i', '--id', required=True)
    parser_client_update.add_argument('-d', '--data', required=True)

    parser_client_delete = client_method_subparsers.add_parser('delete')
    parser_client_delete.add_argument('-i', '--id', required=True)

    args = parser.parse_args()

    if args.mode == 'server':
        server = Server(args.address, args.port)
        server.run()
    elif args.mode == 'client':
        client = Client(args.address, args.port, args.user)
        if args.method == "get":
            client.get(int(args.id))
            exit
        elif args.method == "post":
            client.post(args.data.encode())
            exit
        elif args.method == "update":
            client.update(int(args.id), args.data.encode())
            exit
        elif args.method == "delete":
            client.delete(int(args.id))
            exit