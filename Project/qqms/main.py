import numpy as np
import qiskit
from qiskit_experiments.library import T1
from qiskit_ibm_runtime.fake_provider import FakeBrisbane
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
import qiskit_aer
import warnings
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_experiments.library.characterization.t2hahn import T2Hahn
import matplotlib.pyplot as plt

#get rid of annoying warning over nothing!
warnings.filterwarnings("ignore", message="Options .* have no effect in local testing mode.")


def T1Test(numQubits, liveBackend=False, backend=None, customT1=False, customT1Data=None, delayStart=0, delayEnd=50,
           delaySpread=100):
    if liveBackend is False:
        backendProvider = FakeBrisbane()
        #build noise model
        noise_model = NoiseModel.from_backend(
            backendProvider, gate_error=False, readout_error=False, thermal_relaxation=True)

        #apply noise model
        simulator = AerSimulator.from_backend(backendProvider, noise_model=noise_model)
    else:
        #setup backend for nonlocal
        service = QiskitRuntimeService(instance="ibm-q/open/main")
        simulator = service.backend(backend)
        #backendProvider = service

    ##get known T1 data
    #qubitT1Data = []
    #if customT1 is False:
    #    for i in range(numQubits):
    #        qubitT1Data.append(backendProvider.qubit_properties(i).t1)
    #else:
    #    qubitT1Data = customT1Data

    #set delays for experiment
    delays = []
    for i in range(numQubits):
        delays.append((np.linspace(delayStart, delayEnd, delaySpread) * 1e-5))

    #create and run experiments on each qubit
    experimentArray = []
    for i in range(numQubits):
        #create experiment
        experiment = T1(physical_qubits=(i,), delays=delays[i])
        experiment.set_transpile_options(scheduling_method='asap')

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


def T2Test(numQubits, liveBackend=False, backend=None, delayStart=0, delayEnd=50, delaySpread=100):
    if liveBackend is False:
        backendProvider = FakeBrisbane()
        #build noise model
        noise_model = NoiseModel.from_backend(
            backendProvider, gate_error=False, readout_error=False, thermal_relaxation=True)
        #apply noise model
        simulator = AerSimulator.from_backend(backendProvider, noise_model=noise_model)
    else:
        #setup backend for nonlocal
        service = QiskitRuntimeService(instance="ibm-q/open/main")
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


# Parameters for the T2Test
numQubits = 127  # Number of qubits to test
liveBackend = False  # Set to True if using a live backend
backend = None  # Specify your backend if using a live backend
delayStart = 0  # Start delay
delayEnd = 50  # End delay
delaySpread = 100  # Number of delay points

# Run the T2 Test
experimentArray = T2Test(numQubits, liveBackend, backend, delayStart, delayEnd, delaySpread)

# Prepare data for plotting
t2_values = []
std_devs = []
qubit_indices = []

for i, result in enumerate(experimentArray):
    if result[0] is not None:  # Check if the nominal value is not None
        t2_values.append(result[0])
        std_devs.append(result[1])
        qubit_indices.append(i)

# Convert lists to numpy arrays for better handling
t2_values = np.array(t2_values)
std_devs = np.array(std_devs)

# Plotting
plt.figure(figsize=(10, 6))
plt.bar(qubit_indices, t2_values, yerr=std_devs, capsize=5, color='lightblue', alpha=0.7, label='T2 Values')
plt.xticks(qubit_indices)  # Set x-ticks to be the qubit indices
plt.title('T2 Hahn Echo Experiment Results')
plt.xlabel('Qubit Index')
plt.ylabel('T2 Time (s)')
plt.grid(axis='y', linestyle='--')
plt.legend()
plt.show()
