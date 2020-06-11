#!/usr/bin/env python
import socket, sys, select
import logging

logging.basicConfig(filename='coordinator.log',level=logging.DEBUG)

HOST = '127.0.0.1'
PORT = 9009
BUFFER_SIZE = 4096
SOCKET_LIST = []

coordinator_state = None # Anyone of ["PT","C", "F","A"]
rCount = 0
cCount = 0
amountTransfer = 0 

def numberOfSockets():
    return len(SOCKET_LIST) - 2

def chat_server():
    global coordinator_state
    # Using IPv4 and TCP protocl
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)

    server_socket.bind((HOST,PORT))
    server_socket.listen(100)

    # adding server socket to the list of all available sockets
    SOCKET_LIST.append(server_socket)

    print "Chat server started on port " + str(PORT)

    while True:
        # select funtion return a list of sockets that are ready to read, we also set the time out to 0 so that it will never block
        ready_to_read,ready_to_write_,in_error = select.select(SOCKET_LIST, [],[],0)

        for s in ready_to_read:

            if s == server_socket: # means a new client is trying to join
                new_sock, addr = server_socket.accept()
                SOCKET_LIST.append(new_sock)

                print "Client (%s, %s) connected." % addr
                broadcast(server_socket, new_sock, "[%s:%s] just joined the room!\n" % addr)
            else:
                try:
                    data = s.recv(BUFFER_SIZE)
                    print data
                    if data:
                        flag = 0
                        spliting = list(data.split("##"))
                        if int(spliting[0]) == 1:
                            state = spliting[1]
                            if state == "F":
                                if coordinator_state == "C":
                                    print "Coordinator Fails"
                                    logging.info("Coordinator Fails")
                                    flag = 1
                                    broadcast(server_socket, None, "\r" + '[' + str(s.getpeername()) + '] ' + "Coordinator Failed. Wait for the Recovery\n")
                                    logging.info("\r" + '[' + str(s.getpeername()) + '] ' + "Coordinator Failed. Wait for the Recovery")
                                    sendSecific(server_socket, s, "Commit the transaction in the database\n")                            
                                    logging.info("Commit the transaction in the database")    
                                elif coordinator_state == "PT":
                                    if rCount == len(SOCKET_LIST) - 2:
                                        print "Coordinator Fails"
                                        logging.info("Coordinator Fails")
                                        flag = 1
                                        broadcast(server_socket, None, "\r" + '[' + str(s.getpeername()) + '] ' + "Coordinator Failed. Wait for the Recovery blocking all nodes\n")
                                        logging.info("\r" + '[' + str(s.getpeername()) + '] ' + "Coordinator Failed. Wait for the Recovery blocking all nodes\n")
                                        sendSecific(server_socket, s, "Recover from the failure and change state to commit\n")
                                        logging.info("Recover from the failure and change state to commit")    
                                    else:
                                        flag = 1
                                        sendSecific(server_socket, s, "Recover from the failure \n") 
                                        logging.info("Recover from the failure")                              
                                print "Failed State"
                            elif state == "D":
                                if coordinator_state == "C" and cCount  == len(SOCKET_LIST) - 2:
                                    fullamount = amountTransfer * (len(SOCKET_LIST) - 2)
                                    sendSecific(server_socket,s,"fullAmount: " + str(fullamount) + "\n")
                                    flag = 0
                                    rCount = 0
                                    cCount = 0
                                    amountTransfer = 0
                                    coordinator_state = None
                                else:
                                    flag = 1
                                    print("Transaction should be commited first")
                                    logging.info("Transaction should be commited first")
                            elif state == "NM":
                                print "Normal State"
                            elif coordinator_state == None:
                                if state == "PT":
                                    rCount = 0
                                    cCount = 0
                                    coordinator_state = state
                                    amountTransfer = int(list(data.split("amount:"))[-1])
                                    print "Entered prepare Transaction state"
                                    logging.info("Entered prepare Transaction state")
                                else:
                                    flag = 1
                                    print "Starting state should be prepare transaction"
                                    logging.info("Starting state should be prepare transaction")
                            else:
                                if coordinator_state == "PT":
                                    if rCount != len(SOCKET_LIST) - 2:
                                        print "Wait for Ready Configuration"
                                        logging.info("Wait for Ready Configuration")
                                        flag = 1
                                    else:
                                        coordinator_state = state
                                elif coordinator_state == "C":
                                    if cCount != len(SOCKET_LIST) - 2:
                                        print "Wait for Commit from All site"
                                        logging.info("Wait for Commit from All site")
                                        flag = 1
                                    else:
                                        coordinator_state = state        
                        else:
                            state = spliting[1]
                            if coordinator_state == "PT":
                                if state == "F":
                                    flag = 1
                                    print "Sending Abort message" 
                                    broadcast(server_socket, None, "\r" + '[' + str(s.getpeername()) + '] ' + "Node failed. Abort the transaction\n")
                                    logging.info("\r" + '[' + str(s.getpeername()) + '] ' + "Node failed. Abort the transaction\n")
                                    rCount = 0
                                    cCount = 0
                                    coordinator_state = None
                                    amountTransfer = 0
                                elif state == "R":
                                    rCount += 1
                                else:
                                    flag = 1
                                    print "First it should be in ready state"
                                    # logging.info("First it should be in ready state")
                            elif coordinator_state == "C":
                                if state == "F":
                                    sendSecific(server_socket,s," Commit the Transaction T\n")
                                elif state == "C":
                                    cCount += 1
                                else:
                                    flag = 1
                                    print "Transaction is ready it should be in commit state" 
                            else:
                                pass
                            # site_state[str(s.getpeername()] = state
                        # if int(spliting[0]) == 1 and flag == 0:
                        #     logging.info(data)
                        data = spliting[len(spliting)-1]
                        # broadcast the data to all other client sockets
                        if flag == 0:
                            broadcast(server_socket, s, "\r" + '[' + str(s.getpeername()) + '] ' + data)
                    else:
                        # may have a connection problem, so we remove the client socket
                        if s in SOCKET_LIST:
                            SOCKET_LIST.remove(s)

                        # broadcast a message to other clients informing that this client has left
                        broadcast(server_socket, s, "Client (%s, %s) is offline\n" % addr)

                except:
                    broadcast(server_socket, s, "Client (%s, %s) is offline\n" % addr)
                    # print "Client (%s,%s) is offline"%addr
                    # s.close()
                    # SOCKET_LIST.remove(s)
                    continue

    server_socket.close()

def broadcast(server_socket, sock, message):
    """ Broadcasts chat message to all peers

    Args:
        server_socket: the server socket
        sock: the client socket sending the message
        message: the actual chat message
    """

    for socket in SOCKET_LIST:
        # send the message only to the peers
        if socket != server_socket and socket != sock:
            try:
                socket.send(message)
            except:
                # perhaps disconnected
                socket.close()

                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)

def sendSecific(server_socket, sock, message):
    for socket in SOCKET_LIST:
        # send the message only to the peers
        if socket != server_socket and socket == sock:
            try:
                socket.send(message)
            except:
                # perhaps disconnected
                socket.close()

                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)


if __name__ == "__main__":
    sys.exit(chat_server())
