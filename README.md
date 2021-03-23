# The case for model-driven interpretability of delay-based congestion control protocols

### Table of Contents

- [Description](#description)
- [Instructions](#Instructions)
- [Necessary Steps](#necessary_Steps)
- [References](#references)
- [Author Info](#author-info)

---

## Description

A novel modeling approach that allows us to simplify a congestion control algorithm’s behavior into a guided random walk over a two-dimensional Markov model.

## Instructions
Can be run either on real network or MahiMahi. Follow the following instructions to install MahiMahi.

#### Installation
```sh
$ git clone https://github.com/ravinet/mahimahi
$ cd mahimahi
$ ./autogen.sh
$ ./configure
$ make
$ sudo make install
$ sudo sysctl -w net.ipv4.ip_forward=1
```
See also -[mahimahi.mit.edu] (http://mahimahi.mit.edu/)

Get python3 incase you have the older version
```sh
$ sudo apt-get update
$ sudo apt -y upgrade
```
Also install Matplotlib plotting library for Python:
```sh
$sudo apt-get install python3-matplotlib
```
The protocols folder hold the necessary files for each protocol in use i.e., (Verus and Copa [generiCC]). 

#### Channel Traces

To train a stochastic two-dimensional discrete-time Markov model for a chosen protocol, The protocol's performance must be observed for large sample of cellular traces covering a wide range of diverse scenarios. These traces are all placed in a folder called Traces. 

#### Logging & Protocol runs
The protocol behavior is captured by logging the set of congestion windows and their experienced correlated delays in each run over the Channel traces. For each congestion control protocol (Copa and Verus), there is a seperate file to run. For-example for Verus protocol, Run the following command
```sh
$sudo python runVerusmultiple.py
```
This script calls another script called "run.py", which includes the server and client connectivity commands for the protocol chosen (Verus or Copa). 

The python script shall generate an output directory "Verus_training". The output files contains logs for congestion-window sizes, Uplink and Downlink delays and losses. 

(For Verus, an extra step is required to combine the 'Receiver.out' and 'Verus.out' output log-files obtained from the runs into a single file (for each run). To achieve this, run the following script:
```sh
$ python combine_verus.py
```

 This will create a combined log file for each trace in their respective folders For-example; channel_log_0-combined.out)

## Necessary Steps
#### Steps 1 [Pre-processing]:

After the logs are created, Run the following command
```sh
$ sudo python preprocess_verus.py 1000
```
The system argument '1000' is the number of files you want to process (Usually this is the number of channels you have run the protocol for. A high number of channel traces is desired for training). The preprocess_verus.py script will generate processed data files for each trace-trial used by congestion control protocol chosen. For-example: the "processed-0-verus.out" contains the quantized form of all state trasitions (di,wi) obtained for the channel trace by verus. 

(preprocess_copa.py shall be used for copa)

#### Steps 2 [Training]:

After the data is processed; run the following command to create the transition matrix for the chosen congestion control protocol.
```sh
 $	python3 train.py  verus --numfiles 1000 
```
 The first argument is the protocol chosen while the second argument is needed for the number of files to select.
 Note that, it is important to specify the boundries for delay and window values at this stage. The training script makes sure the delay and window values falls within specific boundry limits (i.e.,DP_MIN, DP_MAX, WP_MIN and WP_MAX). These limits are chosen by looking at cdfs of both the delays and Windows in pre-processed files.

 After running the above command, csv file of the transition matrix for the chosen protocol is created  in the training directory. 

#### Steps 3 [Matrix Analysis]:
	
In order to refine the transition matrix to proper probability values for different state trasitions, run the following command
```sh
$ python3 matrix_analysis.py training/verus/transmatrix-verus-N001.csv --outfolder verus_matrix --clean
```
This will create a directory named verus_matrix, where the verus transition matrix is stored by the name "verus-N001-transMatrix.csv" along with matrices'probability
distributions across the transition space in a pdf representing the states the protocol mostly operates in. 

[Back To The Top](#the-case-for-model-driven-interpretability-of-delay-based-congestion-control-protocols)

## Running MDI version of a Protocol Vs Its Native version

After the transition matrix is created; run the following .sh file 
```sh
$ sudo ./run.sh
```
Make sure you uncomment the congestion control protocol you are interested in. For-example, here we are only interested in comparing verus native to the model-verus, so we will uncomment verus and model-verus. Also the path to transition matrix should be provided in the run.sh file, for the model version of the protocol chosen.

Note that, the model version of both verus and copa uses gmcc in the subdirectory called protocols. 

[Back To The Top](#the-case-for-model-driven-interpretability-of-delay-based-congestion-control-protocols)

---

## References
Muhammad Khan, Yasir Zaki, Shiva Iyer, Talal Ahmad, Thomas Poetsch, Jay Chen, Anirudh Sivaraman, and Lakshmi Subramanian. 2021. The case for model-driven interpretability of delay-based congestion control protocols. SIGCOMM Comput. Commun. Rev. 51, 1 (01/31/2021), 18–25. DOI:https://doi.org/10.1145/3457175.3457179

[Back To The Top](#the-case-for-model-driven-interpretability-of-delay-based-congestion-control-protocols)

---

## Corresponding Authors

- Yasir Zaki - (https://nyuad.nyu.edu/en/academics/divisions/science/faculty/yasir-zaki.html)

- Muhammad Khan - (https://comnetsad.github.io/people.html)

- Thomas Poetsch- (https://nyuad.nyu.edu/en/academics/divisions/science/faculty/thomas-potsch.html)

[Back To The Top](#the-case-for-model-driven-interpretability-of-delay-based-congestion-control-protocols)
