import numpy as np
from qiskit_experiments.library import T1
from qiskit_ibm_runtime.fake_provider import FakeAthensV2
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
import warnings
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_experiments.library.characterization.t2hahn import T2Hahn
import boto3
from datetime import datetime

#get rid of annoying warning over nothing!
warnings.filterwarnings("ignore", message="Options .* have no effect in local testing mode.")


def T1Test(numQubits, apiToken, liveBackend=False, backend=None, delayStart=0, delayEnd=50, delaySpread=100):
    if liveBackend is False:
        backendProvider = GenericBackendV2(num_qubits=numQubits);
        #build noise model
        noise_model = NoiseModel.from_backend(
            backendProvider, gate_error=False, readout_error=False, thermal_relaxation=True)

        #apply noise model
        simulator = AerSimulator.from_backend(backendProvider, noise_model=noise_model)
    else:
        #setup backend for nonlocal
        service = QiskitRuntimeService(token=apiToken, instance="ibm-q/open/main")
        simulator = service.backend(backend)
        #backendProvider = service

    #set delays for experiment
    delays = []
    for i in range(numQubits):
        delays.append((np.linspace(delayStart, delayEnd, delaySpread) * 1e-5))

    #create and run experiments on each qubit
    experimentArray = []
    for i in range(numQubits):
        #create experiment
        experiment = T1(physical_qubits=(i,), delays=delays[i])
        experiment.set_transple_options(scheduling_method='asap')

        #run experiment
        experimentData = experiment.run(backend=simulator).block_for_results()

        #get T1 result
        t1_result = experimentData.analysis_results("T1")

        #add the T1 nominal value and standard deviation to experimentArray
        if t1_result:
            experimentArray.append([
                t1_result.value.nominal_value,
                t1_result.value.std_dev
            ])
        else:
            experimentArray.append([None, None])
    return experimentArray


def T2Test(numQubits, backend, apiToken, liveBackend=False, delayStart=0, delayEnd=50, delaySpread=100):
    if liveBackend is False:
        backendProvider = GenericBackendV2(num_qubits=numQubits);
        #build noise model
        noise_model = NoiseModel.from_backend(
            backendProvider, gate_error=False, readout_error=False, thermal_relaxation=True)
        #apply noise model
        simulator = AerSimulator.from_backend(backendProvider, noise_model=noise_model)
    else:
        #setup backend for nonlocal
        service = QiskitRuntimeService(token=apiToken, instance="ibm-q/open/main")
        simulator = service.backend(backend)
        #backendProvider = service
    #set delays
    delays = []
    for i in range(numQubits):
        delays.append(np.linspace(delayStart, delayEnd, delaySpread) * 1e-5)

    #create and run experiments on each qubit
    experimentArray = []
    for i in range(numQubits):
        experiment = T2Hahn(physical_qubits=(i,), delays=delays[i])
        experiment.set_transpile_options(scheduling_method='asap')
        experimentData = experiment.run(backend=simulator).block_for_results()
        #get T1 result
        t2_result = experimentData.analysis_results("T2")

        #add the T2 nominal value and standard deviation to experimentArray
        if t2_result:
            experimentArray.append([
                t2_result.value.nominal_value,
                t2_result.value.std_dev
            ])
        else:
            experimentArray.append([None, None])
    return experimentArray


def addT1ToTable(tableName, QubitNum, T1Value, T1Std, ACCESS_KEY, SECRET_KEY, REGION_NAME):
    dynamodb = boto3.client(
        'dynamodb',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION_NAME
    )
    table = dynamodb.Table(tableName)

    timestamp = datetime.now()

    table.put_item(
        Item={
            'QubitNumber': QubitNum,
            'Timestamp': timestamp,
            'T2Value': T1Value,
            'StandardDeviation': T1Std
        }
    )


def addT2ToTable(tableName, QubitNum, T2Value, T2Std, ACCESS_KEY, SECRET_KEY, REGION_NAME):
    dynamodb = boto3.client(
        'dynamodb',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION_NAME
    )
    table = dynamodb.Table(tableName)

    timestamp = datetime.now()

    table.put_item(
        Item={
            'QubitNumber': QubitNum,
            'Timestamp': timestamp,
            'T2Value': T2Value,
            'StandardDeviation': T2Std
        }
    )
