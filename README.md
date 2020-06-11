# 2-Phase-Commit-Protocol
Code is done with respect to centralised architecture having client and server side helping in simulation of 2 Phase Protocol

# Run
First run server using

    python2 server.py

As the code is running on localhost you can also change the IP address and port in the server file 

Then start running the client:

    python2 client.py <server ip> <server port> <coordinator flag>

<coordinator flag> can have two values either 0 or 1 

0 - Means the site does not want to be coordinator

1 - Means the site wants to become a coordinator

For this code if you run without changing

    <server ip> : 127.0.0.1

    <server port> : 9009
