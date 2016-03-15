#! /usr/bin/python
# -*- coding: utf-8 -*-

import socket
import sys
import select
import re
 
size = 1024
uname = ''
try:
    g_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # socket for keyinterrupt exception handling
except socket.error, msg:
    sys.stderr.write("[ERROR] %s\n" % msg[1])
    sys.exit(1)

def login(ssock):
    global uname
    uname = raw_input('please enter your username: ')
    passwd = raw_input('please enter your password: ')
    
    msg = 'login '+ uname + ' ' + passwd 
    ssock.send(msg)
    welcome_msg = ssock.recv(size) 
    print welcome_msg
    if welcome_msg == '\nunknown username\n' or welcome_msg == '\nyou are already online\n':
        #ssock.close()
        return False

    if welcome_msg == '\ninvalid password\n':
        #while True:
        #    passwd = raw_input('please enter your password: ')
        #    ssock.send(passwd)
        #    welcome_msg = ssock.recv(size) 
        #    if welcome_msg == '\ninvalid password\n':
        #ssock.close()
        return False

    return True    

def input_loop(ssock):
    global uname
    print '\n', uname+'> '
    sockets_listen = [ssock, sys.stdin] # socket list for select 
    msg_client = ''
    while True:
        inputready,outputready,exceptready = select.select(sockets_listen,[],[]) 
        for current in inputready: 
            if current == ssock: # new msg from server
                print ssock.recv(size)
                print '\n', uname+'> '
            elif current == sys.stdin: # user types new input   
                try:    
                    msg_client += raw_input() + '\n'
                except (EOFError): # detect EOF, send msg to server
                    ssock.send(msg_client)
                    msg_client = msg_client.lstrip()
                    cmd = re.split(r'[\n ]+', msg_client)
                    if cmd[0] == 'logout': # detect logout command, close client program
                        print 'You have logged out, thanks\n'
                        ssock.close()
                        return 
                    msg_client = ''
                    print '\n', uname+'> '    
            else:
                print 'unknown socket'



def main(): 
    port = int(sys.argv[1]) # get port number
  
    try:
        g_server_sock.connect(('', port))
    except socket.error, msg:
        sys.stderr.write("[ERROR] %s\n" % msg[1])
        exit(1)
    if login(g_server_sock) == False:
        return

    input_loop(g_server_sock)
    
if __name__ == '__main__': 
    try:
        main()
    except KeyboardInterrupt:
        # handle client logout
        g_server_sock.send('logout')
        print '\nclient receive ctrl+C\n'    
    