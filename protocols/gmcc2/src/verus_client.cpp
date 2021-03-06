/*
  MIT License
  Copyright (c) 2021 Muhammad Khan, Yasir Zaki, Shiva Iyer, Talal Ahmad, 
  Thomas Poetsch, Jay Chen, Anirudh Sivaraman, and Lakshmi Subramanian
  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:
  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.
  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
*/

#include "verus.hpp"

int len_inet;                // length
int s,err;

char* port;
char* srvr_addr;
unsigned int delay = 0;

bool receivedPkt = false;
bool terminate = false;

struct sockaddr_in adr_srvr;
struct sockaddr_in adr_srvr2;
struct sockaddr_in adr;

struct timeval startTime;
struct timeval currentTime;
double relativeTime;
double t;



pthread_t timeout_tid;
pthread_t sending_tid;

typedef struct {
  udp_packet_t *pdu;
  long long seconds;
  long long millis;
} sendPkt;

std::vector<sendPkt*> sendingList;
pthread_mutex_t lockSendingList;

boost::asio::io_service io;
boost::asio::deadline_timer timer (io, boost::posix_time::milliseconds(SS_INIT_TIMEOUT));

static void displayError(const char *on_what) {
  fputs(strerror(errno),stderr);
  fputs(": ",stderr);
  fputs(on_what,stderr);
  fputc('\n',stderr);
  exit(1);
}

void TimeoutHandler( const boost::system::error_code& e) {
    int z;

    if (e) return;

    z = sendto(s,"Hallo", strlen("Hallo"), 0, (struct sockaddr *)&adr_srvr2, len_inet);
    if ( z < 0 )
      displayError("sendto(Hallo)");

    //update timer and restart
    timer.expires_from_now (boost::posix_time::milliseconds(1000));
    timer.async_wait(&TimeoutHandler);

    return;
}

void* sending_thread (void *arg)
{
	
  int s1, z;
  struct timeval timestamp;
  sendPkt *pkt;

  memset(&adr_srvr,0,sizeof adr_srvr);

  adr_srvr2.sin_family = AF_INET;
  adr_srvr2.sin_port = htons(atoi(port));
  adr_srvr2.sin_addr.s_addr =  inet_addr(srvr_addr);

  if ( adr_srvr2.sin_addr.s_addr == INADDR_NONE ) {
    displayError("bad address.");
  }

  s1 = socket(AF_INET,SOCK_DGRAM,0);
  if ( s1 == -1 ) {
    displayError("socket()");
  }

  while (!terminate || relativeTime <= t) {
    gettimeofday(&timestamp,NULL);

    pthread_mutex_lock(&lockSendingList);

    if (sendingList.size() > 0)
       pkt = * sendingList.begin();

    // since tc qdisc command in Linux seems to have some issues when adding delay, we defer the packet here
    if (sendingList.size() > 0 && (timestamp.tv_sec-pkt->seconds)*1000.0+(timestamp.tv_usec-pkt->millis)/1000.0 > delay) {
      // sending ACK
      z = sendto(s1, pkt->pdu, sizeof(udp_packet_t), 0, (struct sockaddr *)&adr_srvr2, len_inet);
      free (pkt->pdu);

      if (z < 0)
        if (errno == ENOBUFS || errno == EAGAIN || errno == EWOULDBLOCK)
          std::cout << "reached maximum OS UDP buffer size\n";
        else
          displayError("sendto(2)");

      sendingList.erase(sendingList.begin());
      pthread_mutex_unlock(&lockSendingList);
    }
    else{
      pthread_mutex_unlock(&lockSendingList);
      usleep(0.01);
    }

    gettimeofday(&currentTime,NULL);
    relativeTime = (currentTime.tv_sec-startTime.tv_sec)+(currentTime.tv_usec-startTime.tv_usec)/1000000.0;
  }

  return NULL;
}

void* timeout_thread (void *arg)
{
  boost::asio::io_service::work work(io);

  timer.expires_from_now (boost::posix_time::milliseconds(SS_INIT_TIMEOUT));
  timer.async_wait(&TimeoutHandler);
  io.run();

  return NULL;
}

int main(int argc,char **argv) {
  int z;
  int i = 1;
  char command[512];
  char tmp[512];

  udp_packet_t *pdu;
  sendPkt *pkt;
  struct timeval timestamp;
  setbuf(stdout, NULL);
  std::ofstream clientLog;

  pthread_mutex_init(&lockSendingList, NULL);

  if (argc < 4) {
    std::cout << "syntax should be ./verus_client <server address> -p <server port> -t <time> [-d <additional link delay in ms>] \n";
    exit(0);
  }

  srvr_addr = argv[1];

  while (i != (argc-1)) { // Check that we haven't finished parsing already
    i=i+1;
    if (!strcmp (argv[i], "-p")) {
      i=i+1;
      port = argv[i];
    }
    else if (!strcmp (argv[i], "-t"))
    {
    	i = i+1;
    	t = std::stod(argv[i]);
    } 
    else if (!strcmp (argv[i], "-d")) {
      i=i+1;
      delay = atoi(argv[i]);
    }else {
      std::cout << "syntax should be ./verus_client <server address> -p <server port> [-d <additional link delay in ms>] \n";
      exit(0);
    }
  }

  gettimeofday(&startTime,NULL);


  memset(&adr_srvr,0,sizeof adr_srvr);

  adr_srvr.sin_family = AF_INET;
  adr_srvr.sin_port = htons(atoi(port));
  adr_srvr.sin_addr.s_addr =  inet_addr(srvr_addr);

  if ( adr_srvr.sin_addr.s_addr == INADDR_NONE ) {
    displayError("bad address.");
  }

  len_inet = sizeof adr_srvr;

  s = socket(AF_INET,SOCK_DGRAM,0);
  if ( s == -1 ) {
    displayError("socket()");
  }

  std::cout << "Sending request to server \n";

  //printf("Sending Hallo to %s:%s\n", srvr_addr, port);
  z = sendto(s,"Hallo", strlen("Hallo"), 0, (struct sockaddr *)&adr_srvr, len_inet);
  if ( z < 0 )
    displayError("sendto(Hallo)");

  // if (pthread_create(&(timeout_tid), NULL, &timeout_thread, NULL) != 0)
  //     std::cout << "can't create thread: " <<  strerror(err) << "\n";

	std::cout<<"here 1";
  if (pthread_create(&(sending_tid), NULL, &sending_thread, NULL) != 0)
      std::cout << "can't create thread: " <<  strerror(err) << "\n";
  



  // starting to loop waiting to receive data and to ACK
  while(!terminate || relativeTime <= t) {
    

    pdu = (udp_packet_t *) malloc(sizeof(udp_packet_t));

    socklen_t len = sizeof(struct sockaddr_in);
    
    z = recvfrom(s, pdu, sizeof(udp_packet_t), 0, (struct sockaddr *)&adr, &len);
    if ( z < 0 )
      std::cout<<"recvfrom(2)";

  	//std::cout<<"here 2";

    if (pdu->ss_id < 0) {
      clientLog.close();
      terminate = true;
    }

    // stopping the io timer for the timeout
    if (!receivedPkt) {
      sprintf (command, "client_%s.out", port);
      clientLog.open(command);
      receivedPkt = true;
      io.stop();
      std::cout << "Connected to server \n";
    }

    gettimeofday(&timestamp,NULL);
    sprintf(tmp, "%ld.%06d, %llu\n", timestamp.tv_sec, timestamp.tv_usec, pdu->seq);
    clientLog << tmp;

    pkt = (sendPkt *) malloc(sizeof(sendPkt));
    pkt->pdu = pdu;
    pkt->seconds = timestamp.tv_sec;
    pkt->millis = timestamp.tv_usec;

    pthread_mutex_lock(&lockSendingList);
    sendingList.push_back(pkt);
    pthread_mutex_unlock(&lockSendingList);

    gettimeofday(&currentTime,NULL);
    relativeTime = (currentTime.tv_sec-startTime.tv_sec)+(currentTime.tv_usec-startTime.tv_usec)/1000000.0;
    //std::cout<<"relativetime:\n";
    //std::cout<<relativeTime;
  }

  std::cout << "Client exiting \n";
  close(s);
  return 0;
}
