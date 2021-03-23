#!/bin/bash

# MIT License
# Copyright (c) 2021 Muhammad Khan, Yasir Zaki, Shiva Iyer, Talal Ahmad, 
# Thomas Poetsch, Jay Chen, Anirudh Sivaraman, and Lakshmi Subramanian
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

time=300
dir=Evaluations
matrixpath=./verus_matrix/verus-N001-transMatrix.csv # specify the correct Matrix path here

for trace in cellularGold rapidGold highwayGold; do 
	i=1
	end=20
 	while [ $i -le $end ]; do
 		echo $trace

# 		#Verus and Model Verus
		python run.py -tr $trace -t $time --name $trace$i --dir $dir --algo verus
 		python run.py -tr $trace -t $time --name $trace --dir $dir --algo modelVerus --pathtomatrix $matrixpath
 		mv client_60001.out $dir/modelVerus/$trace$i/

		#Copa and Model copa
		# python run.py -tr $trace -t $time --name $trace$i --dir $dir --algo copa
		# python run.py -tr $trace -t $time --name $trace$i --dir $dir --algo modelCopa
		# mv client_60001.out $dir/modelCopa/$trace$i/

    	i=$(($i+1))

 	done
		
done
