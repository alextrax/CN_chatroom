• A brief description
	This is a python written chatroom program consists of a server and a client.

• Development environment
	Python-2.7.10

• Instructions 
	server: 
		python server.py [port]
	client:
		python client.py [server ip] [port]	

• Sample commands 
	who 										- show anyone who's online
	broadcast <message> 						- broadcast message 
	send (<user> <user> ... <user>) <message>   - send private message to multiple users
	send <user> <message>						- send private message
	logout										

• Additional functionalities 
	1. Support offline message
		Use 'send' command to message anyone who is not online, 
		the message will be showed at the receiver's next log in
	2. Support multi-line message
		Example command: 
		send
		columbia

		Hi

		how are

		you?	