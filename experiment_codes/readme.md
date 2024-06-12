## Initial Phase

The  package used are recorded in requirements.txt, which can be installed with:

```shell
pip install -r requirements.txt
```



In directory **src**:

0_extractKERASEXPORT.py： Locate class definition files in directory Keras-3.1.0, The result is saved in data/globalNameRecord.json.

1_CollectAPIsFromDocs.py: Extract layer API list from Keras official website. The result is saved in data/globalNameRecord.json.

2_findClsDefs.py: Extract function definition of layer APIs from class definition files recorded in data/globalNameRecord.json. The result is saved in data/funcDef.pickle.

3_locateArgs.py: Extract the parameter list from the function definitions. The result is saved in data/funcDefwithArgList.pickle.

4_createArgDict.py: Create parameter dict for each layer API. The result is saved in directory data/argDir.

5_Instrument.py: Instrument the Keras source code and generate 3 new envirionments: 

​		1）instruct_collect: to collect initial data 

​		2）instruct_PACO: to reproduce our approach 

​		3）instruct_FFcollect: to initialize FreeFuzz seed pool

​		4) instruct_FreeFuzz: to execute FreeFuzz

## Step1. PACO initialize

```shell
cd data/instrument-collect
pytest keras/layers
cd ../../data/instrument-PACO
python 1_MergeDict.py
```

Start another terminal to start the execution server:

```shell
cd data/instrument-PACO
python 0_startServer.py
```

After the server starts, continue the initialization:

```shell
python 2_preprocessing.py
```



## Step2. FreeFuzz initialize

FreeFuzz utils MongoDB to contain data, therefore you should [install and run MongoDB](https://docs.mongodb.com/manual/installation/) first.

Then to collect the data,

```shell
cd data/instrument-FFcollect
python preprocess/process_data.py tf
pytest keras/layers
```



## Step3. Reproduce RQ1

#### FreeFuzz Experiment:

```shell
cd data/instrument-FreeFuzz
python FreeFuzz.py --conf demo_tf.conf
```

The results are saved in instrument-FreeFuzz/freefuzzResults/

#### PACO & Random Experiment:

firstly start the execution server

```shell
cd data/instrument-PACO
python 0_startServer.py
```

Then start the PACO:

```shell
python 3.1_ArtificialBenchmark_PACO.py
```

And the Random Experiment:

```shell
python 3.0_ArtificialBenchmark_RandomBaseline.py
```

The results are saved in directory RQ1Res/

## Step4. Reproduce RQ2

The PACO result is reproduced in Step 3.

To reproduce the other results, firstly start the execution server.

```shell
cd data/instrument-PACO
python 0_startServer.py
```

Then execute the experiments:

```shell
python 3.2_PACO-Ext.py
python 3.3_PACO-mFIC.py
python 3.4_PACO-init.py
```

The results are saved in directory RQ2Res/

## Step5. Reproduce RQ3

Firstly start the execution server.

```shell
cd data/instrument-PACO
python 0_startServer.py
```

Then execute the experiments:

```
python 4_RealBechmark_Random.py
python 4_RealBenchmark_PACO.py
```

The results are saved in directory RQ3Res/
