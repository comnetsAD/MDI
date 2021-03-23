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

int s, err;
int port;

int NUM_WND;
int NUM_DELAY;
int MIN_WND;
int MAX_WND;
int STEP_WND;
int MIN_DELAY;
int MAX_DELAY;
int STEP_DELAY;

double **MODEL_MATRIX;

double wLast=-10;
double deltaDBar = 1.0;
double wMax = 0.0;

double dMax = 0.0;
double dMaxLast = 20.0;
double dMaxLastLast = 20.0;

double wBar = 10;
double wBarLast = 10;
double wBarLastLast = 10;

double dTBar = 0.0;
double dEst = 0.0;
int S = 0;
int ssId = 0;
double dMin = 1000.0;

double delay;
int curveStop = MAX_W_DELAY_CURVE;
int maxWCurve = 0;
long long pktSeq = 0;
unsigned long long seqLast = 0;

double timeToRun;

bool slowStart = true;
bool exitSlowStart = false;
bool haveSpline = false;
bool terminate = false;
bool lossPhase = false;

char command[512];
char *name;
char *matrixCSV;

pthread_mutex_t lockSendingList;
pthread_mutex_t lockSPline;
pthread_mutex_t restartLock;
pthread_mutex_t missingQueue;

pthread_t receiver_tid, delayProfile_tid, sending_tid, timeout_tid;

struct sockaddr_in adr_clnt;
struct sockaddr_in adr_clnt2;

struct timeval startTime;
struct timeval lastAckTime;

socklen_t len_inet;
spline1dinterpolant spline;

std::atomic<long long> wCrt(0);
std::atomic<long long> tempS(0);
std::vector<double> delaysEpochList;
std::map <unsigned long long, long long> sendingList;
std::map <int, udp_packet_t*> missingsequence_queue;

// output files
std::ofstream receiverLog;
std::ofstream lossLog;
std::ofstream verusLog;
std::ofstream delwinlog;

// Boost timeout timer
boost::asio::io_service io;
boost::asio::deadline_timer timer (io, boost::posix_time::milliseconds(SS_INIT_TIMEOUT));

void segfault_sigaction(int signal, siginfo_t *si, void *arg)
{
    std::cout << "caught seg fault \n";

    verusLog.close();
    lossLog.close();
    receiverLog.close();

    exit(0);
}

static void displayError(const char *on_what) {
    fputs(strerror(errno),stderr);
    fputs(": ",stderr);
    fputs(on_what,stderr);
    fputc('\n',stderr);

    std::cout << "Error \n";

    exit(0);
}

void write2Log (std::ofstream &logFile, std::string arg1, std::string arg2, std::string arg3, std::string arg4, std::string arg5) {
  double relativeTime;
  struct timeval currentTime;

  gettimeofday(&currentTime,NULL);
    relativeTime = (currentTime.tv_sec-startTime.tv_sec)+(currentTime.tv_usec-startTime.tv_usec)/1000000.0;

    logFile << relativeTime << "," << arg1;

    if (arg2 != "")
      logFile << "," << arg2;
    if (arg3 != "")
      logFile << "," << arg3;
    if (arg4 != "")
      logFile << "," << arg4;
    if (arg5 != "")
      logFile << "," << arg5;

    logFile << "\n";

    return;
}


udp_packet_t *
udp_pdu_init(int seq, unsigned int packetSize, int w, int ssId) {
    udp_packet_t *pdu;
    struct timeval timestamp;

    if (packetSize <= sizeof(udp_packet_t)) {
        printf("defined packet size is smaller than headers");
        exit(0);
    }

    pdu = (udp_packet_t*)malloc(packetSize);

    if (pdu) {
        pdu->seq = seq;
        pdu->w = w;
        pdu->ss_id = ssId;
        gettimeofday(&timestamp,NULL);
        pdu->seconds = timestamp.tv_sec;
        pdu->millis = timestamp.tv_usec;
    }
  return pdu;
}

void TimeoutHandler( const boost::system::error_code& e) {
    double timeouttimer = 0;

    if (e) return;

    // write2Log (lossLog, "Timeout", "", "", "", "");

    if (seqLast == 0) {
        // write2Log (lossLog, "Restart", "lost first packet", "", "", "");
        return;
    }

    if (slowStart) {
        slowStart = false;
        // write2Log (lossLog, "Exit slow start", "timeout", "", "", "");
    }
    else {
        // timeout means that no packets in flight, so we should reset the packets in flight
        // we should also change the sequence last (last acked packet) to the last sent packet
        lossPhase = true;
        wCrt = 0;
        dEst = dMin;

        pthread_mutex_lock(&lockSendingList);
        if (sendingList.size() > 0) {
            // write2Log (lossLog, "clearing sending list because of timeout", "", "", "", "");
            seqLast = sendingList.rbegin()->first;
            sendingList.clear();
        }
        pthread_mutex_unlock(&lockSendingList);

        // resetting the missingsequence queue
        pthread_mutex_lock(&missingQueue);
        missingsequence_queue.clear();
        pthread_mutex_unlock(&missingQueue);
    }

    //update timer and restart
    timeouttimer=fmin (MAX_TIMEOUT, fmax((5*delay), MIN_TIMEOUT));
    timer.expires_from_now (boost::posix_time::milliseconds(timeouttimer));
    timer.async_wait(&TimeoutHandler);

    return;
}

int calcSi (double wBar) {
    int S;
    int n;

    n = (int) ceil(dTBar/(EPOCH/1000.0));

    if (n > 1)
        S = (int) fmax (0, (wBar+wCrt*(2-n)/(n-1)));
    else
        S = (int) fmax (0, (wBar - wCrt));

    return S;
}

void* sending_thread (void *arg)
{
    int i, ret;
    int sPkts;
    udp_packet_t *pdu;
    //struct timeval currentTime;

    while (!terminate) {
        while (tempS > 0) {
            sPkts = tempS;
            tempS = 0;

            for (i=0; i<sPkts; i++) {
                pktSeq ++;
                pdu = udp_pdu_init(pktSeq, MTU, wBar, ssId);
                //gettimeofday(&currentTime,NULL);

                ret = sendto(s, pdu, MTU, MSG_DONTWAIT, (struct sockaddr *)&adr_clnt, len_inet);

                if (ret < 0) {
                    // if UDP buffer of OS is full, we exit slow start and treat the current packet as lost
                    if (errno == ENOBUFS || errno == EAGAIN || errno == EWOULDBLOCK) {
                        if (slowStart) {
                            lossPhase = true;
                            exitSlowStart = true;
                            wBar = 0.49 * pdu->w; // this is so that we dont switch exitslowstart until we receive packets that are not from slow start
                            slowStart = false;

                            // this packet was not sent we should decrease the packet seq number and free the pdu
                            pktSeq --;
                            free(pdu);

                            // write2Log (lossLog, "Exit slow start", "reached maximum OS UDP buffer size", std::to_string(wCrt), "", "");
                            break;
                        }
                        else {
                            // this is normal sending, OS UDP buffer is full, discard this packet and treat as lost
                            wBar = fmax(1.0, VERUS_M_DECREASE * wBar);

                            // this packet was not sent we should decrease the packet seq number and free the pdu
                            pktSeq --;
                            free(pdu);

                            // write2Log (lossLog, "Loss", "reached maximum OS UDP buffer size", std::to_string(errno), "", "");
                            break;
                        }
                    }
                    else
                        displayError("sendto(2)");
                }
                // storing sending packet info in sending list with sending time
                pthread_mutex_lock(&lockSendingList);
                sendingList[pdu->seq]=pdu->w;
                pthread_mutex_unlock(&lockSendingList);
                free (pdu);

                // sending one new packet -> increase packets in flight
                wCrt ++;
            }
            if (tempS > 0 && !slowStart)
                write2Log (lossLog, "Epoch Error", "couldn't send everything within the epoch. Have more to send", std::to_string(tempS.load()), std::to_string(slowStart), "");
        }
    }
    return NULL;
}


void updateUponReceivingPacket (double delay, int w) {

    if (wCrt > 0)
        wCrt --;

    // processing the delay and updating the verus parameters and the delay curve points
    delaysEpochList.push_back(delay);
    dTBar = delay;

    // updating the minimum delay
    if (delay < dMin)
        dMin = delay;

    // not to update the wList with any values that comes within the loss phase
    if (!lossPhase) {
        if (maxWCurve < w)
            maxWCurve = w;
    }
    else {    // still in loss phase, received an ACK, do similar to congestion avoidance
        wBar += 1.0/wBar;
    }
    return;
}

void createMissingPdu (int i) {
    udp_packet_t* pdu;
    pdu = (udp_packet_t *) malloc(sizeof(udp_packet_t));
    struct timeval currentTime;

    gettimeofday(&currentTime,NULL);
    pdu->seq = i;
    pdu->seconds = currentTime.tv_sec;
    pdu->millis = currentTime.tv_usec;

    pthread_mutex_lock(&lockSendingList);
    pdu->w = sendingList.find(pdu->seq)->second;
    pthread_mutex_unlock(&lockSendingList);

    pthread_mutex_lock(&missingQueue);
    missingsequence_queue[i]=pdu;
    pthread_mutex_unlock(&missingQueue);

    return;
}

void removeExpiredPacketsFromSeqQueue (struct timeval receivedtime) {
    bool timerExpiry = false;
    udp_packet_t* pdu;
    double missingsequence_delay;

    // accessing the first element in the queue to check if its expired
    pdu = missingsequence_queue.begin()->second;
    missingsequence_delay = (receivedtime.tv_sec-pdu->seconds)*1000.0+(receivedtime.tv_usec-pdu->millis)/1000.0;

    while (missingsequence_delay >= MISSING_PKT_EXPIRY) { // missing packet is treated lost after MISSING_PKT_EXPIRY
        // this means that we have identified a packet loss
        // storing the w of the first missing pdu expiry to use it in the multiplicative decrease
        if (!timerExpiry) {
            timerExpiry = true;

            if (!lossPhase) { // if its a new loss phase then we do multiplicative decrease, otherwise it belonges to the same loss phase
                lossPhase = true;

                // write2Log (lossLog, "Missing packet expired", std::to_string(pdu->seq), "", "", ""); // we are only recordering the first missing packet expiry per loss phase

                // get the w of the lost packet and do multiplicative decrease
                wBar = fmax(1.0, fmin(wBar, VERUS_M_DECREASE * pdu->w));
            }
        }
        // erase the pdu from the missing queue as well as from the sendinglist
        if (missingsequence_queue.find(pdu->seq) != missingsequence_queue.end()) {
            missingsequence_queue.erase(pdu->seq);
        }

        pthread_mutex_lock(&lockSendingList);
        if (sendingList.find(pdu->seq) != sendingList.end()) {
            sendingList.erase(pdu->seq);
        }
        pthread_mutex_unlock(&lockSendingList);

        free(pdu);

        if (wCrt > 0)
            wCrt--;

        missingsequence_delay = 0;

        if (missingsequence_queue.size() > 0) {
            pdu = missingsequence_queue.begin()->second;
            missingsequence_delay = (receivedtime.tv_sec-pdu->seconds)*1000.0+(receivedtime.tv_usec-pdu->millis)/1000.0;
        }
    }
    return;
}

void* receiver_thread (void *arg)
{
    unsigned int i;
    double timeouttimer=0.0;
    socklen_t len_inet;
    udp_packet_t *pdu;
    struct timeval receivedtime;

    len_inet = sizeof(struct sockaddr_in);

    sprintf (command, "%s/Losses.out", name);
    lossLog.open(command);
    sprintf (command, "%s/Receiver.out", name);
    receiverLog.open(command);

    pdu = (udp_packet_t *) malloc(sizeof(udp_packet_t));

    while (!terminate) {

        if (recvfrom(s, pdu, sizeof(udp_packet_t), 0, (struct sockaddr *)&adr_clnt2, &len_inet) < 0)
            displayError("Receiver thread error");

        gettimeofday(&receivedtime,NULL);
        delay = (receivedtime.tv_sec-pdu->seconds)*1000.0+(receivedtime.tv_usec-pdu->millis)/1000.0;

        //update timer and restart
        timeouttimer=fmin (MAX_TIMEOUT, fmax((5*delay), MIN_TIMEOUT));
        timer.expires_from_now (boost::posix_time::milliseconds(timeouttimer));
        timer.async_wait(&TimeoutHandler);

        write2Log (receiverLog, std::to_string(pdu->seq), std::to_string(delay), std::to_string(wCrt), std::to_string(wBar), "");

        // Receiving exactly the next sequence number, everything is ok no losses
        if (pdu->seq == seqLast+1) {
            updateUponReceivingPacket (delay, pdu->w);
        }
        else if (pdu->seq < seqLast) {
            // received a packet with seq number smaller than the anticipated one (out of order). Need to check if that packet is there in the missing queue
            pthread_mutex_lock(&missingQueue);
            if (missingsequence_queue.find(pdu->seq) != missingsequence_queue.end()) {
                missingsequence_queue.erase(pdu->seq);
                updateUponReceivingPacket (delay, pdu->w);
            }
            else
                // write2Log (lossLog, "Received an expired out of sequence packet ", std::to_string(pdu->seq), std::to_string(seqLast), "", "");
            pthread_mutex_unlock(&missingQueue);
        }
        else { // creating an out of sequence packet and inserting it to the out of sequence queue
            for (i=seqLast+1; i<pdu->seq; i++)
                createMissingPdu (i);
            updateUponReceivingPacket (delay, pdu->w);
        }

        // setting the last received sequence number to the current received one for next packet arrival processing
        // making sure we dont take out of order packet
        if (pdu->seq >= seqLast+1 && pdu->ss_id == ssId) {
            seqLast = pdu->seq;
            gettimeofday(&lastAckTime,NULL);
        }

        // freeing that received pdu from the sendinglist map
        pthread_mutex_lock(&lockSendingList);
        if (sendingList.find(pdu->seq) != sendingList.end()) {
            sendingList.erase(pdu->seq);
        }
        pthread_mutex_unlock(&lockSendingList);
        pthread_mutex_unlock(&restartLock);
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

struct arrayElement {
    double val;
    int idx;
};

double readMatrix () {
    char buffer[60000] ;
    FILE *fstream = fopen(matrixCSV,"r");
    char *record,*line;
    int i=0,j=0;


    if(fstream == NULL)
    {
      printf("\n file opening failed ");
      return -1 ;
    }

    while((line=fgets(buffer,sizeof(buffer),fstream))!=NULL)
    {
        record = strtok(line,",");
        while(record != NULL)
        {
            printf ("%d %d %s %f \n", i, j, record, atof(record));
            fflush(stdout);
            
            if (i == 0) {
                if (j==0)
                    NUM_WND = atoi(record);
                else if (j==1)
                    MIN_WND = atoi(record);
                else if (j==2)
                    MAX_WND = atoi(record);
                else if (j==3)
                    STEP_WND = atoi(record);
                else if (j==4)
                    NUM_DELAY = atoi(record);
                else if (j==5)
                    MIN_DELAY = atoi(record);
                else if (j==6)
                    MAX_DELAY = atoi(record);
                else if (j==7) {
                    STEP_DELAY = atoi(record);
                    MODEL_MATRIX = (double **) malloc(NUM_WND * NUM_DELAY * sizeof(double *));
                    for (int a = 0; a < NUM_WND*NUM_DELAY; a++) {
                        MODEL_MATRIX[a] = (double *) malloc(NUM_WND*NUM_DELAY * sizeof(double));
                    }
                }
                record = strtok(NULL,",");
                j++;
            }
            else {
                MODEL_MATRIX[i-1][j++] = atof(record) ;
                record = strtok(NULL,",");
            }
        }
        ++i ;
        j=0;
    }

    printf ("%d %d %d %d %d %d \n", NUM_WND, NUM_DELAY, MIN_DELAY, MAX_DELAY, MIN_WND, MAX_WND);
    fflush(stdout);

    return 0 ;
}

double modelDriven_computeWND (double a, double b, double c)
{
    int row, tmp_idx;
    double d, tmp, w;
    double r = ((double) rand() / (RAND_MAX));
    double cdf_sum = 0;
    struct arrayElement *array = (struct arrayElement *)malloc(NUM_WND*sizeof(struct arrayElement));

    int sIndex = NUM_WND*c;
    int eIndex = NUM_WND*(c+1);

    row = NUM_WND*a + b;

    printf ("row %d \n", row);
    // write2Log (lossLog, std::to_string(a), std::to_string(b), std::to_string(c), std::to_string(wBar), std::to_string(r));

    while (row > 0) {
        // creating the sublist
        for (int i = 0; i < NUM_WND; i++){
            array[i].val = MODEL_MATRIX[row][sIndex+i];
            array[i].idx = i;
            printf ("%d %f \n", i, MODEL_MATRIX[row][sIndex+i]);
        }

        // sorting the transition probabilities
        for (int i = 0; i < NUM_WND; ++i) {
            for (int j = i + 1; j < NUM_WND; ++j) {
                if (array[i].val > array[j].val) {
                    tmp = array[i].val;
                    tmp_idx = array[i].idx;
                    array[i] = array[j];
                    array[j].val = tmp;
                    array[j].idx = tmp_idx;
                }
            }
        }

        for (int i = 0; i < NUM_WND; i++){
            cdf_sum = cdf_sum + array[i].val;
            // printf ("random %f %f \n", r, cdf_sum);
            if (r < cdf_sum) {
                printf ("%d %d %d %d %f \n", array[i].idx, STEP_WND, MIN_WND, array[i].idx*STEP_WND+MIN_WND, wBarLast);
                if (wBarLast > 1)
                    w = ((array[i].idx*STEP_WND+MIN_WND)/log10(wBarLast)+100)*wBarLast/100;
                else
                    w = ((array[i].idx*STEP_WND+MIN_WND)/log10(wBarLast+1)+100)*wBarLast/100;
                return w;
                }
        }
        row -=1;
    }
    //return wBarLast;
    return 1.0;
}

double ewma (double vals, double delay, double alpha) {
    double avg;

    // checking if the value is negative, meanning it has not been udpated
    if (vals < 0)
        avg = delay;
    else
        avg = vals * alpha + (1-alpha) * delay;

    return avg;
}


int main(int argc,char **argv) {

    int i=0;
    double bufferingDelay;
    double relativeTime=0;
    double wBarTemp;
    bool dMinStop=false;
    bool gotACK = false;
    double a,b,c;

    double delayAvg = 20;
    double wndAvg = 1;

    char dgram[512];             // Recv buffer

    struct stat info;
    struct sigaction sa;
    struct sockaddr_in adr_inet;
    struct timeval currentTime;

    // catching segmentation faults
    memset(&sa, 0, sizeof(struct sigaction));
    sigemptyset(&sa.sa_mask);
    sa.sa_sigaction = segfault_sigaction;
    sa.sa_flags   = SA_SIGINFO;
    sigaction(SIGSEGV, &sa, NULL);

    if (argc < 8) {
        std::cout << "syntax should be ./verus_server -name NAME -p PORT -tr PATH_to_MATRIXcsv -t TIME (sec) \n";
        exit(0);
    }

    while (i != (argc-1)) {
        i=i+1;
        if (!strcmp (argv[i], "-name")) {
            i=i+1;
            name = argv[i];
            }
        else if (!strcmp (argv[i], "-p")) {
            i=i+1;
            port = atoi (argv[i]);
            }
        else if (!strcmp (argv[i], "-t")) {
            i=i+1;
            timeToRun = std::stod(argv[i]);
            }
        else if (!strcmp (argv[i], "-tr")) {
            i=i+1;
            matrixCSV = argv[i];
            }
        else {
            std::cout << "syntax should be ./verus_server -name NAME -p PORT -t TIME (sec) \n";
            exit(0);
        }
    }

    readMatrix();

    s = socket(AF_INET,SOCK_DGRAM,0);
    if ( s == -1 )
        displayError("socket error()");

    memset(&adr_inet,0,sizeof adr_inet);
    adr_inet.sin_family = AF_INET;
    adr_inet.sin_port = htons(port);
    adr_inet.sin_addr.s_addr = INADDR_ANY;

    if ( adr_inet.sin_addr.s_addr == INADDR_NONE )
        displayError("bad address.");

    len_inet = sizeof(struct sockaddr_in);

    if (bind (s, (struct sockaddr *)&adr_inet, sizeof(adr_inet)) < 0)
        displayError("bind()");

    std::cout << "Server " << port << " waiting for request\n";

    // waiting for initialization packet
    if (recvfrom(s, dgram, sizeof (dgram), 0, (struct sockaddr *)&adr_clnt, &len_inet) < 0)
        displayError("recvfrom(2)");

    if (stat (name, &info) != 0) {
        sprintf (command, "exec mkdir %s", name);
        system(command);
    }
    sprintf (command, "%s/Verus.out", name);
    verusLog.open(command);
    sprintf (command, "%s/delwinStates.out", name);
    delwinlog.open(command);
    // getting the start time of the program, to make relative timestamps
    gettimeofday(&startTime,NULL);

    // create mutex
    pthread_mutex_init(&lockSendingList, NULL);
    pthread_mutex_init(&lockSPline, NULL);
    pthread_mutex_init(&restartLock, NULL);

    // starting the threads
    if (pthread_create(&(timeout_tid), NULL, &timeout_thread, NULL) != 0)
        std::cout << "can't create thread: " <<  strerror(err) << "\n";
    if (pthread_create(&(receiver_tid), NULL, &receiver_thread, NULL) != 0)
        std::cout << "Can't create thread: " << strerror(err);
    if (pthread_create(&(sending_tid), NULL, &sending_thread, NULL) != 0)
        std::cout << "Can't create thread: " << strerror(err);

    // sending the first for slow start
    tempS = 0;

    std::cout << "Client " << port << " is connected\n";
    gettimeofday(&lastAckTime,NULL);

    while (relativeTime <= timeToRun) {
        gotACK = false;

        gettimeofday(&currentTime,NULL);
        relativeTime = (currentTime.tv_sec-startTime.tv_sec)+(currentTime.tv_usec-startTime.tv_usec)/1000000.0;

        // Checking if we have an missing packets that have expired so that we can trigger a loss
        pthread_mutex_lock(&missingQueue);
        if (missingsequence_queue.size() > 0)
            removeExpiredPacketsFromSeqQueue(currentTime);
        pthread_mutex_unlock(&missingQueue);

        printf ("GOT ACKs %d \n", delaysEpochList.size());
        if (delaysEpochList.size() > 0) {
            gotACK = true;
            //Talal : dMax accumulate is actually average
            dMax = *std::max_element(delaysEpochList.begin(),delaysEpochList.end());
            // dMax = std::accumulate(delaysEpochList.begin(), delaysEpochList.end(), 0.0) / delaysEpochList.size();
            //dMax = *std::min_element(delaysEpochList.begin(),delaysEpochList.end());
            delaysEpochList.clear();
            // write2Log (lossLog, "gotAcks", std::to_string(dMax), std::to_string(dMaxLast),"","");
        }
        else {
            bufferingDelay = (currentTime.tv_sec-lastAckTime.tv_sec)*1000.0+(currentTime.tv_usec-lastAckTime.tv_usec)/1000.0;
            dMax = bufferingDelay;
            dMax = fmax (dMaxLast, bufferingDelay);
            // write2Log (lossLog, "bufferingDelay", std::to_string(dMax), std::to_string(dMaxLast), std::to_string(bufferingDelay), "");
            //dMax = dMaxLast;
        }

        // only first verus epoch, dMaxLast is intialized to -10
        if (dMaxLast == -10)
            dMaxLast = dMax;

        //delayAvg = 0.95*dMax+0.05*delayAvg;
        //dMax = delayAvg;

        // Model driven CC comes here --------
        printf ("dmax dmaxLast %f %f \n", dMax, dMaxLast);

        a = ((dMaxLast/dMaxLastLast)*100-100)*log10(dMaxLastLast);
        b = ((wBarLast/wBarLastLast)*100-100)*log10(wBarLastLast);
        c = ((dMax/dMaxLast)*100-100)*log10(dMaxLast);

        delwinlog<<std::to_string(c)<<"\n";

        std::cout<<c<<"\n";

        // write2Log (lossLog, "", std::to_string(c), std::to_string(dMax), std::to_string(dMaxLast), std::to_string(dMaxLastLast));
        // write2Log (lossLog, "---", std::to_string(a), std::to_string(b), std::to_string(c), "");

        if (c > MAX_DELAY) { // || dMax > 1000.0) { 
            // model Verus
            //wBarTemp = std::fmax (1.5, wBar - 5);
            /* Model Copa */
            //wBarTemp = std::fmax (2, wBar - 4.22); // 0.175  /* set wBar-5.2 for cellularGold*/
            //For cellularGold
            wBarTemp =  wBar*0.975;
            //For highwayGold
            //wBarTemp =  wBar*0.95;      //0.93 //0.93//0.948//*0.95//*0.91;
             //For RapidGold
           // wBarTemp =  wBar*0.95;
            //wBarTemp =  std::fmax (2,wBar-2);
            write2Log (lossLog, "> max delay", std::to_string(c), std::to_string(dMax), std::to_string(dMaxLast), std::to_string(dMaxLastLast));
        }
        else if (c < MIN_DELAY) {
            // model verus
            //wBarTemp = wBar + 20;

            // model copa
            //For cellularGold
            //wBarTemp=wBar+22;
            //For highwayGold
          // wBarTemp=wBar+9.5;           //13  //12 //12//9.8//11//+13;
            //For RapidGold
            wBarTemp=wBar+21; 

            write2Log (lossLog, "< min delay", std::to_string(c), std::to_string(dMax), std::to_string(dMaxLast), std::to_string(dMaxLastLast));
        }

        // if (c > MAX_DELAY) { // || dMax > 1000.0) {
        //     write2Log (lossLog, "> max delay", std::to_string(c), std::to_string(dMax), std::to_string(dMaxLast), std::to_string(dMaxLastLast));
        //     c = MAX_DELAY;
        // }
        // else if (c < MIN_DELAY) {
        //     write2Log (lossLog, "< min delay", std::to_string(c), std::to_string(dMax), std::to_string(dMaxLast), std::to_string(dMaxLastLast));
        //     c = MIN_DELAY;
        // }

        //if (1 == 1) {
        else {

            write2Log(lossLog,"matrix c",std::to_string(c),"","","");

            if (a < MIN_DELAY)
                a = 0;
            else if (a > MAX_DELAY)
                a = (int) ((MAX_DELAY - MIN_DELAY) / STEP_DELAY) ;
            else
                a = (int) ((a - MIN_DELAY)/STEP_DELAY);

            if (b < MIN_WND)
                b = 0;
            else if (b > MAX_WND)
                b = (int) ((MAX_WND - MIN_WND) / STEP_WND) ;
            else
                b = (int) ((b - MIN_WND)/STEP_WND);

            printf ("-- a,b,c %f %f %f \n", a, b, c);

            if (c < MIN_DELAY)
                c = 0;
            else if (c > MAX_DELAY)
                c = (int) ((MAX_DELAY - MIN_DELAY) / STEP_DELAY) ;
            else
                c = (int) ((c - MIN_DELAY)/STEP_DELAY);

            wBarTemp = modelDriven_computeWND(a,b,c);
            //printf ("wBar wBarTemp %f %f \n", wBar, wBarTemp);

            // ---------------------------------
        }

        wBar = fmax (1.0, wBarTemp);
        // wBar = ewma(Wtmp, wBar, 0.2);

        S = calcSi (wBar);
        printf ("%d %f %f \n", S, wBar, wBarTemp);
        tempS += S;

        if (gotACK) {
            dMaxLastLast = dMaxLast;
            dMaxLast = dMax;
        }
        wBarLastLast = wBarLast;
        wBarLast = wBar;

        //double b=  ((wBar/wLast)*100-100)*log10(wLast);

        write2Log (verusLog, std::to_string(wCrt), std::to_string(wBar), std::to_string(S), "", "");
        usleep (EPOCH);
    }

    verusLog.close();
    lossLog.close();
    receiverLog.close();
    io.stop();
    ssId = -1;
    tempS = 1;

    usleep (1000000);
    terminate = true;
    usleep (1000000);

    std::cout << "Server " << port << " is exiting\n";
    close(s);

    return 0;
}
