import numpy as np
from qruise.toolset.libraries.rydberg.rydbergsystem import RydbergSystem


from qruise.toolset.signal import gates
from qruise.toolset.libraries.rydberg.envelopes import rect_envelope


def name_rx_gate(angle: float, atom: str) -> str:
    angle = np.around(angle, 6)
    return f"rx_{str(angle)}_{atom}"

def name_ry_gate(angle: float, atom: str) -> str:
    angle = np.around(angle, 6)
    return f"ry_{str(angle)}_{atom}"

def name_cz_gate(atom1: str, atom2: str) -> str:
    return f"cz_{atom1}{atom2}"

def create_rx_gate(ryd_system: RydbergSystem, angle: float, atom: str, rabi_amplitude: float) -> gates.Instruction:
    # print("Multiple of pi?", 1/(angle/np.pi))
    original_angle = angle
    angle = np.around(angle, 6)
    rabi = rabi_amplitude
    abs_angle = np.around(np.abs(angle), 6)

    if angle < 0:
        rabi = -rabi_amplitude
    t_gate = abs_angle/(2 * np.pi * rabi_amplitude)
    t_gate = np.around(t_gate, 9)# round(t_gate * 1e8) * 1e-8
    # print("T_gate", t_gate)
    if t_gate < 1e-9:
        print("Original angle", original_angle)
        print("Atom", atom)
        print("T_gate is too small")
        t_gate = 1e-9
    gate = gates.Instruction(
        name=name_rx_gate(angle, atom),
    t_end=t_gate,
    targets=[int(atom)],
    channels=[f"rx{atom}"],
    qiskit_name="rx"
    )
    ryd_system.add_instruction(instruction=gate, envelope=rect_envelope("rectangular_envelope", amp=2 * np.pi * rabi*1e-6, t_final=t_gate), drive_name=f"rx{atom}")
    #gate.add_component(rect_envelope("rectangular_envelope", amp=rabi, t_final=t_gate), chan=f"rxQ{atom}")
    gate.ideal = None
    return gate

def create_ry_gate(ryd_system: RydbergSystem, angle: float, atom: str, rabi_amplitude: float) -> gates.Instruction:
    # print("Multiple of pi?", 1/(angle/np.pi))
    original_angle = angle
    angle = np.around(angle, 6)
    rabi = rabi_amplitude
    abs_angle = np.around(np.abs(angle), 6)
    if angle < 0:
        rabi = -rabi_amplitude
    t_gate = abs_angle/(2 * np.pi * rabi_amplitude)
    t_gate = np.around(t_gate, 9)# round(t_gate * 1e8) * 1e-8
    # print("T_gate", t_gate)
    if t_gate < 4e-9:
        print("Original angle", original_angle)
        print("Atom", atom)
        print("T_gate is too small")
        t_gate = 4e-9
    gate = gates.Instruction(
        name=name_ry_gate(angle, atom),
        t_end=t_gate,
        targets=[int(atom)],
        channels=[f"ry{atom}"],
        qiskit_name="ry"
    )
    gate.ideal = None
    ryd_system.add_instruction(instruction=gate, envelope=rect_envelope("rectangular_envelope", amp=2 * np.pi * rabi*1e-6, t_final=t_gate), drive_name=f"ry{atom}")
    #gate.add_component(rect_envelope("rectangular_envelope", amp=rabi, t_final=t_gate), chan=f"ry{atom}")
    return gate

def create_cz_gate(ryd_system: RydbergSystem, atom1: str, atom2: str, rabi_amplitude: float = 2e6) -> list[gates.Instruction]:
    t_pi = np.round(1 / (2 * rabi_amplitude) * 1e9) * 1e-9

    cz12_1 = gates.Instruction(
            name=f"{name_cz_gate(atom1, atom2)}_1",
            t_end=t_pi,
            channels=[f"rydbergx{atom1}"],
            targets=[int(atom1), int(atom2)],
            qiskit_name="cz",
            
        )
    cz12_1.ideal = None
    ryd_system.add_instruction(instruction=cz12_1, envelope=rect_envelope("rectangular_envelope", amp=2 * np.pi * rabi_amplitude*1e-6, t_final=t_pi), drive_name=f"rydbergx{atom1}")
    #cz12_1.add_component(rect_envelope("rectangular_envelope", amp=rabi_amplitude, t_final=t_pi), chan=f"rx{atom1}")
    cz12_2 = gates.Instruction(
        name=f"{name_cz_gate(atom1, atom2)}_2",
        t_end=2 * t_pi,
        channels=[f"rydbergx{atom2}"],#[f"rx{atom2}"],
        targets=[int(atom1), int(atom2)],
        qiskit_name="cz",
    )
    cz12_2.ideal = None
    ryd_system.add_instruction(instruction=cz12_2, envelope=rect_envelope("rectangular_envelope", amp=2 * np.pi * rabi_amplitude*1e-6, t_final=2 * t_pi), drive_name=f"rydbergx{atom2}")
    #cz12_2.add_component(rect_envelope("rectangular_envelope", amp=rabi_amplitude, t_final=2 * t_pi), chan=f"rx{atom2}")
    cz12_3 = gates.Instruction(
        name=f"{name_cz_gate(atom1, atom2)}_3",
        t_end=t_pi,
        channels=[f"rydbergx{atom1}"],#[f"rx{atom1}"],
        targets=[int(atom1), int(atom2)],
        qiskit_name="cz",
    )
    cz12_3.ideal = None
    ryd_system.add_instruction(instruction=cz12_3, envelope=rect_envelope("rectangular_envelope", amp=2 * np.pi * rabi_amplitude*1e-6, t_final=t_pi), drive_name=f"rydbergx{atom1}")
    #cz12_3.add_component(rect_envelope("rectangular_envelope", amp=rabi_amplitude, t_final=t_pi), chan=f"rx{atom1}")
    return [cz12_1, cz12_2, cz12_3]

def create_instructions(rydberg_system: RydbergSystem, circuit, rabi_amplitude: float = 2e6) -> list[gates.Instruction]:
    gates_list = []
    for _, c in enumerate(circuit):
        if "ry" in c.operation.name:
            gates_list.append(create_ry_gate(ryd_system=rydberg_system, angle=c.operation.params[0], atom=c.qubits[0]._index, rabi_amplitude=rabi_amplitude))
        elif "rx" in c.operation.name:
            # ryd_system: RydbergSystem, angle: float, atom: str, rabi_amplitude: float
            gates_list.append(create_rx_gate(ryd_system=rydberg_system, angle=c.operation.params[0], atom=c.qubits[0]._index, rabi_amplitude=rabi_amplitude))
        elif c.operation.name == "cz":
            gates_list.extend(create_cz_gate(ryd_system=rydberg_system, atom1=c.qubits[0]._index, atom2=c.qubits[1]._index, rabi_amplitude=rabi_amplitude))
        else:
            print(c.operation.name)
    return gates_list