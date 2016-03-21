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

def login(ssock, retry = 0): #0:success, 1:unknown or duplicate, 2:invalid passwd, 3:block user 
    global uname
    if retry == 0:
        uname = raw_input('please enter your username: ')
    passwd = raw_input('please enter your password: ')
    
    msg = 'login '+ uname + ' ' + passwd 
    ssock.send(msg)
    welcome_msg = ssock.recv(size) 
    print welcome_msg
    if welcome_msg == '\nunknown username\n' or welcome_msg == '\nyou are already online\n':
        #ssock.close()
        return 1
    elif welcome_msg == '\ninvalid password\n':
        return 2
    elif welcome_msg == '\nYOU ARE BLOCKED!!\n':
        return 3   
    else:    
        return 0    

def input_loop(ssock):
    global uname
    print '\n', uname+'> '
    sockets_listen = [ssock, sys.stdin] # socket list for select 
    msg_client = ''
    while True:
        inputready,outputready,exceptready = select.select(sockets_listen,[],[]) 
        for current in inputready: 
            if current == ssock: # new msg from server
                server_msg = ssock.recv(size)
                print server_msg
                if server_msg == '@@@AUTO_LOGOUT@@@': # automatically kicked out by server
                    return
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
    IP = sys.argv[1] # IP address
    port = int(sys.argv[2]) # get port number
  
    try:
        g_server_sock.connect((IP, port))
    except socket.error, msg:
        sys.stderr.write("[ERROR] %s\n" % msg[1])
        exit(1)

    ret = login(g_server_sock)
    if ret == 2:  # wrong passwd, retry
        while True:
            r = login(g_server_sock, 1)    
            if r == 0: # retry login
                break
            elif r == 3: # being blocked
                return    

    elif ret == 1: # 1:unknown or duplicate user
        return 

    elif ret == 3: # 3:user being blocked
        return   

    input_loop(g_server_sock)
    
if __name__ == '__main__': 
    try:
        main()
    except KeyboardInterrupt:
        # handle client logout
        g_server_sock.send('logout')
        print '\nclient receive ctrl+C\n'    
    