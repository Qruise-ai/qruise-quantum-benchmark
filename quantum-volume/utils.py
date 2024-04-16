from qiskit import transpile
import numpy as np
from qiskit.quantum_info import Statevector
from qiskit.circuit.library import QuantumVolume as QuantumVolumeCircuit

def _check_threshold(nheavies, ncircuits, nshots):
    """Evaluate adjusted threshold inequality for quantum volume.
    Args:
        nheavies (int): Total number of heavy outputs measured from device
        ncircuits (int): Number of different square circuits run on device
        nshots (int): Number of shots per circuit
    Returns:
        Bool:
            True if heavy output probability is > 2/3 with 97% certainty,
            otherwise False
    """

    numerator = nheavies - 2*np.sqrt(nheavies*(nshots-(nheavies/ncircuits)))
    return bool(numerator/(ncircuits*nshots) > 2/3)

def _get_heavy_outputs(counts):
    """Extract heavy outputs from counts dict.
    Args:
        counts (dict): Output of `.get_counts()`
    Returns:
        list: All states with measurement probability greater
              than the mean.
    """
    # sort the keys of `counts` by value of counts.get(key)
    sorted_counts = sorted(counts.keys(), key=counts.get)
    # discard results with probability < median
    heavy_outputs = sorted_counts[len(sorted_counts)//2:]
    return heavy_outputs

def quantum_volume(device, nqubits, ncircuits, nshots, use_backend_properties=True):
    """Try to achieve 2**nqubits quantum volume on device.
    Args:
        device (qiskit.providers.Backend): Device to test.
        nqubits (int): Number of qubits to use for test.
        ncircuits (int): Number of different circuits to run on the device.
        nshots (int): Number of shots per circuit.
    Returns:
        Bool
            True if device passes test, otherwise False.
    """
    def get_ideal_probabilities(circuit):
        """Simulates circuit behaviour on a device with no errors."""
        state_vector = Statevector.from_instruction(
                circuit.remove_final_measurements(inplace=False)
            )
        return state_vector.probabilities_dict()

    def get_real_counts(circuit, backend, shots, use_backend_properties=True):
        """Runs circuit on device and returns counts dict."""
        if use_backend_properties:
            t_circuit = transpile(circuit, backend)
        else:
            t_circuit = transpile(circuit, basis_gates=backend.configuration().basis_gates)
        job = backend.run(t_circuit,
                          shots=shots,
                          memory=True)
        return job.result().get_counts()

    # generate set of random circuits
    qv_circuits = [ QuantumVolumeCircuit(nqubits) for _ in range(ncircuits)]

    nheavies = 0  # number of measured heavy outputs
    for circuit in qv_circuits:
        # simulate circuit
        ideal_heavy_outputs = _get_heavy_outputs(
            get_ideal_probabilities(circuit)
        )
        # run circuit on device
        circuit.measure_all()
        real_counts = get_real_counts(circuit, device, nshots, use_backend_properties=use_backend_properties)
        # record whether device result is in the heavy outputs
        for output, count in real_counts.items():
            if output in ideal_heavy_outputs:
                nheavies += count

    # do statistical check to see if device passes test
    is_pass = _check_threshold(nheavies, ncircuits, nshots)
    # calculate percentage of measurements that are heavy outputs
    percent_heavy_outputs = nheavies*100/(ncircuits * nshots)

    print(f"Quantum Volume: {2**nqubits}\n"
          f"Percentage Heavy Outputs: {percent_heavy_outputs:.1f}%\n"
          f"Passed?: {is_pass}\n")
    return is_pass