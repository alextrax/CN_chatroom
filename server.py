#! /usr/bin/python
# -*- coding: utf-8 -*-

import socket
import select 
import sys
import hashlib
import re
from datetime import datetime

size = 1024 
user_pass = dict() # dictionary: key = username, value = password
logout_time = dict() # dictionary: key = username, value = logout time
user_sock = dict() # dictionary: key = username, value = user sock
ip_block = dict() # dictionary: key = ip, value = block endtime
login_fail = dict() # dictionary: key = uname, value = count
offline_msg = [] # list of off_message
sockets_listen = [] # sock list for select


class off_message:
    def __init__(self, receiver, msg):
        self.receiver = receiver
        self.msg = msg

def parse_user_pass(): # read user_pass.txt and save it to dictionary user_pass
    f = open('user_pass.txt')
    for line in f:
        line = line.rstrip('\n') # remove '\n'
        info = line.split(' ') 
        user_pass[info[0]] = info[1]
         
      
def handle_login(csock, data): # 0:success, 1:unknown user, 2:duplicate, 3:wrong
    info = data.split(' ')
    uname = info[1]
    passwd = info[2]
    print 'uname = ' + uname
    print 'passwd = ' + passwd
    if uname not in user_pass: # unknown user
        csock.send('\nunknown username\n')
        sockets_listen.remove(csock)
        return 1

    if uname in user_sock:
        csock.send('\nyou are already online\n')
        sockets_listen.remove(csock)
        return 2 # already online

    hash_object = hashlib.sha1(passwd.encode())
    hex_dig = hash_object.hexdigest()
    print(hex_dig)

    if hex_dig == user_pass[uname]: # user login success
        user_sock[uname] = csock # add username and corresponding socket
        csock.send('\n*** WELCOME TO CHATROOM (press ctrl+D to submit your command) ***\n')
        if uname in logout_time:
            del logout_time[uname] # remove last logout time

        new_offline_msg = list()
        has_off_msg = 0
        msg =''
        global offline_msg
        for i in offline_msg:
            if i.receiver == uname:
                msg += i.msg + '\n'
                has_off_msg = 1
            else:
                new_offline_msg.append(i)

        if has_off_msg == 1:
            csock.send('\nYou\'ve got offline message:\n')
            csock.send(msg)
            offline_msg = new_offline_msg        
            
        return 0
    else: # wrong password
        csock.send('\ninvalid password\n')
        sockets_listen.remove(csock)
        return 3     

def handle_logout(csock):
    logout_success = ''
    for key in user_sock.iterkeys():
        if(user_sock[key] == csock):
            print 'logout user', key
            logout_success = key
         

    if logout_success != '':
        del user_sock[logout_success]
        logout_time[logout_success] = datetime.now()
    else:
        print 'logout failed: can\'t find user\n'    


def handle_broadcast(csock, data):
    cmd = re.split(r'broadcast[\n| ]+', data, 1) # only split the first broadcast
    msg = '<broadcast> \n'+ get_uname_from_sock(csock) + '> \n' + cmd[1]
    for key in user_sock.iterkeys():
        if(user_sock[key] == csock):
            pass # don't need to broadcast to the broadcaster
        else:
            user_sock[key].send(msg)

def get_uname_from_sock(sock):
    for key in user_sock.iterkeys():
        if(user_sock[key] == sock):
            return key

    return 'unknown'        

def handle_send(csock, data):
    cmd = re.split(r'send[\n| ]+', data, 1) # only split the first 'send'
    receiver = re.search(r"\((.+?)\)", cmd[1], re.DOTALL) # re.DOTALL ==> make '.'' include newline, ? ==> non-greedy search
    if receiver: # receivers with () --> (a, b, c...)
        found = receiver.group(1) # --> a, b, c...
        msg = re.split(r'\((.+?)\)', cmd[1], 1, re.DOTALL) # remove (a, b, c...)
        print 'msg:', msg
        found = found.replace("\n", "")
        found = found.replace(" ", "")
        rlist = found.split(',')
        print 'receiver: ',rlist
        for key in rlist:
            if( key in user_sock):
                user_sock[key].send(get_uname_from_sock(csock) + '> \n' + msg[2])
            else: # receiver is not online
                offmsg = off_message(key, get_uname_from_sock(csock) + '> \n' + msg[2])
                offline_msg.append(offmsg)# save msg to offline_msg
                
    else: # single receiver  
        r = re.split(r'[\n| ]+', cmd[1], 1) # r[0] = the single receiver, r[1] = msg
        print 'single receiver: ',r[0]
        if r[0] in user_sock:
            user_sock[r[0]].send(get_uname_from_sock(csock) + '> \n' + r[1])
        else: # receiver is not online
            offmsg = off_message(r[0], get_uname_from_sock(csock) + '> \n' + r[1])
            offline_msg.append(offmsg)# save msg to offline_msg

def handle_last(csock, minute): 
    if minute == '':
        csock.send('please specify the minute\n') 
        return

    now = datetime.now()
    msg = ''
    try:
        fmin = float(minute)
    except ValueError:
        csock.send('invalid argument: ' + minute)  
        return
        
    for key in logout_time:
        diff = now - logout_time[key]
        diff_min = diff.days * 24 * 60 + diff.seconds/60 
        if diff_min < fmin:
            msg += key + ' '

    for key in user_sock: # include online user
        msg += key + ' '

    csock.send(msg)

def handle_command(csock, data): # parse and distribute commands
    data = data.lstrip()
    cmd = re.split(r'[\n ]+', data)
    #print 'cmd =', cmd
    if cmd[0] == 'who':
        msg = ''
        for key in user_sock:
            msg += key + ' '
        csock.send(msg)

    elif cmd[0] == 'last':
        handle_last(csock, cmd[1])
    elif cmd[0] == 'broadcast':
        handle_broadcast(csock, data)
    elif cmd[0] == 'send':
        handle_send(csock, data)
    elif cmd[0] == 'logout':
        handle_logout(csock)
    elif cmd[0] == 'login':
        handle_login(csock, data)   
    else: # unrecognized command  
        print cmd 
        csock.send('unrecognized command: '+data)

def main():    
    host = ''
    port = int(sys.argv[1])
    asock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # socket for accept new connection 
    asock.bind((host, port))
    asock.listen(50)
    global sockets_listen
    sockets_listen = [asock] # socket list for select 
    parse_user_pass()
    print user_pass
    while True:
        inputready,outputready,exceptready = select.select(sockets_listen,[],[]) 
        print 'detect select sockets'
        for current in inputready:
            if current == asock: # new connection 
                csock, addr = asock.accept()
                sockets_listen.append(csock)
                print "Client Info: ", csock, addr
            else:  # msg from client 
                data = current.recv(size) 
                if data: 
                    #current.send('from server:\n' + data) 
                    print 'msg from client', data
                    handle_command(current, data)
                else: 
                    current.close() 
                    sockets_listen.remove(current)     

if __name__ == '__main__': 
    try:
        main()
    except KeyboardInterrupt:
        print '\nserver receive ctrl+C\n'
    	