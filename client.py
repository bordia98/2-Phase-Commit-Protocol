#!/usr/bin/env python
import sys, socket, select
import server
import logging
import os



def initiateTransaction(s):
    print "How much amount you want to take"
    newamt = input()
    message = "Prepare the transaction T with amount: " + str(newamt)
    message = "1"+ "##" + "PT" + "##" + message +"\n"
    s.send(message)
    sys.stdout.write('<Me> ');
    sys.stdout.flush()
    return newamt

def commitTransaction(s):
    message = "Commit the transaction T"
    message = "1"+ "##" + "C" + "##" + message +"\n"
    s.send(message)
    sys.stdout.write('<Me> ');
    sys.stdout.flush()

def abortTransaction(s):
    global newamt
    message = "Abort the transaction T "
    message = "1"+ "##" + "A" + "##" + message +"\n"
    s.send(message)
    sys.stdout.write('<Me> ');
    sys.stdout.flush()

def coordinatorFail(s):
    message = "Coordinator Fails"
    message = "1"+ "##" + "F" + "##" + message +"\n"
    s.send(message)
    sys.stdout.write('<Me> ');
    sys.stdout.flush()

def transactionDone(s):
    message = "Transaction is completed"
    message = "1"+ "##" + "D" + "##" + message +"\n"
    s.send(message)
    sys.stdout.write('<Me> ');
    sys.stdout.flush()

def SiteFails(s):
    message = "Sites Fails"
    message = "0"+ "##" + "F" + "##" + message +"\n"
    s.send(message)
    sys.stdout.write('<Me> ');
    sys.stdout.flush()

def readyState(s):
    message = "Transaction T is Ready"
    message = "0"+ "##" + "R" + "##" + message +"\n"
    s.send(message)
    sys.stdout.write('<Me> ');
    sys.stdout.flush()

def SiteCommitTransaction(s):
    message = "Transaction T commited at site"
    message = "0"+ "##" + "C" + "##" + message +"\n"
    s.send(message)
    sys.stdout.write('<Me> ');
    sys.stdout.flush()



def chat_client():
    global f2
    global f1
    amounttransfer = 0  
    if (len(sys.argv) < 4):
        print 'Usage: python chat_client.py hostname port coordinator(0/1)'
        sys.exit()

    host = sys.argv[1]
    port = int(sys.argv[2])
    coordinator = int(sys.argv[3])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(86400)

    try:
        s.connect((host,port))
    except:
        print "Failed to connect"
        sys.exit()

    print 'Connected to remote host! You can start chatting now!'
    sys.stdout.write('<Me> ');
    sys.stdout.flush()

    if coordinator == 1:
        logging.basicConfig(filename='coordinator.log',level=logging.DEBUG)

        print "Following are the codes which could be used by the coordinator"
        print "PT : Prepare the Transaction"
        print "C : Commit the Transaction"
        print "A : Abort the Transaction"
        print "D : Transaction is complete"
        print "P : To print the amount at the site"
        print "F : When the coordinator fails"
    else:
        print "Enter Site name"
        name = raw_input()
        name = name +".log"
        file(name,"w+").close()
        logging.basicConfig(filename=name,level=logging.DEBUG)
        print "Following are the codes which could be used by the sites"
        print "R : Replying to when the Transaction is ready"
        print "C : Commit the Transaction at Site"
        print "P : To print the amount at the site"
        print "F : When the site fails"

        
    print "Enter the amount present at this site"
    amount = input()
    adder = 0

    if coordinator == 1:
        message = "1" + "##" + "NM"+"##" +" I am the coordinator \n"
        s.send(message)
        sys.stdout.write('<Me> ');
        sys.stdout.flush()

    while True:
        socket_list = [sys.stdin, s]

        ready_to_read, ready_to_write, in_error = select.select(socket_list,[],[])

        for sock in ready_to_read:
            if sock == s:
                data = sock.recv(4096)
                if not data:
                    print '\nDisconnected from chat server'
                    sys.exit()
                else:
                    splitter = list(data.split("amount:"))
                    if len(splitter) > 1:
                        amounttransfer = int(splitter[1])
                    anotherplitter = list(data.split("fullAmount:"))
                    if len(anotherplitter) > 1:
                        adder = int(anotherplitter[1])
                        amount = amount + adder

                    logging.info(data)
                    sys.stdout.write(data)
                    sys.stdout.write('<Me> ');
                    sys.stdout.flush()
            else:
                if coordinator == 1:
                    code = raw_input()
                    if code == "PT":
                        amounttransfer = initiateTransaction(s)
                    elif code == "C":
                        commitTransaction(s)
                    elif code == "A":
                        abortTransaction(s)
                    elif code == "F":
                        coordinatorFail(s)
                    elif code == "D":
                        transactionDone(s)
                    elif code == "P":
                        print "Amount present in Coordinator site = "  + str(amount)
                    else:
                        pass
                else:
                    code = raw_input()
                    if code == "R":
                        readyState(s) 
                    elif code == "C":
                        amount = amount - amounttransfer
                        SiteCommitTransaction(s)
                    elif code == "F":
                        SiteFails(s)
                    elif code == "P":
                        print "Amount present in this site = " + str(amount)
                    else:
                        pass

if __name__ == "__main__":
    sys.exit(chat_client())
