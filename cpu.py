import pyrtl

#Memblocks
i_mem = pyrtl.MemBlock(bitwidth=32, addrwidth=32, name='i_mem')
d_mem = pyrtl.MemBlock(bitwidth=32, addrwidth=32, name='d_mem', asynchronous = True)
rf    = pyrtl.MemBlock(bitwidth=32, addrwidth=32, name='rf', max_read_ports=3, asynchronous = True)

#Cycle through instructions
pc = pyrtl.Register(bitwidth=32, name ='pc')
jump = pyrtl.WireVector(bitwidth =32, name = 'jump')
#PC next clock value will be incremented by 1 and the jump value
pc.next <<= pc + 1 + jump
#Instruction
instr = pyrtl.WireVector(bitwidth = 32, name = 'instr')
#Feed In Instruction from Instruction Memory
instr <<= i_mem[pc]

#Instruction Components
op = pyrtl.WireVector(bitwidth=6, name = 'op')
rs = pyrtl.WireVector(bitwidth=5, name = 'rs')
rt = pyrtl.WireVector(bitwidth=5, name = 'rt')
rd = pyrtl.WireVector(bitwidth=5, name = 'rd')
funct = pyrtl.WireVector(bitwidth=6, name = 'funct')
immed = pyrtl.WireVector(bitwidth = 16, name = 'immed')

#Instruction Decode
op <<= instr[26:32]
rs <<= instr[21:26]
rt <<= instr[16:21]
rd <<= instr[11:16]
funct <<= instr[0:6]
immed <<= instr[0:16]

#Control Variables
reg_dst = pyrtl.WireVector(bitwidth = 1, name = 'reg_dst')
branch = pyrtl.WireVector(bitwidth = 1, name = 'branch')
reg_write = pyrtl.WireVector(bitwidth = 1, name = 'reg_write')
alu_src = pyrtl.WireVector(bitwidth = 2, name = 'alu_src')
mem_write = pyrtl.WireVector(bitwidth = 1, name = 'mem_write')
mem_to_reg = pyrtl.WireVector(bitwidth = 1, name = 'mem_to_reg')
alu_op = pyrtl.WireVector(bitwidth = 3, name = 'alu_op')

#Control Logic
with pyrtl.conditional_assignment:
    #R Type
    with op == int(0x00):
        #ADD
        with funct == int(0x20):
            reg_dst |= 1
            branch |= 0
            reg_write |= 1
            alu_src |= 0
            mem_write |= 0
            mem_to_reg |= 0
            alu_op |= 0
        #AND
        with funct == int(0x24):
            reg_dst |= 1
            branch |= 0
            reg_write |= 1
            alu_src |= 0
            mem_write |= 0
            mem_to_reg |= 0
            alu_op |= 1
        #SLT
        with funct == int(0x2a):
            reg_dst |= 1
            branch |= 0
            reg_write |= 1
            alu_src |= 0
            mem_write |= 0
            mem_to_reg |= 0
            alu_op |= 4
    #ADDI
    with op == int(0x8):
        reg_dst |= 0
        branch |= 0
        reg_write |= 1
        alu_src |= 1
        mem_write |= 0
        mem_to_reg |= 0
        alu_op |= 0
    #LUI
    with op == int(0xf):
        reg_dst |= 0
        branch |= 0
        reg_write |= 1
        alu_src |= 1
        mem_write |= 0
        mem_to_reg |= 0
        alu_op |= 2
    #ORI
    with op == int(0xd):
        reg_dst |= 0
        branch |= 0
        reg_write |= 1
        alu_src |= 2
        mem_write |= 0
        mem_to_reg |= 0
        alu_op |= 3
    #LW
    with op == int(0x23):
        reg_dst |= 0
        branch |= 0
        reg_write |= 1
        alu_src |= 1
        mem_write |= 0
        mem_to_reg |= 1
        alu_op |= 0
    #SW
    with op == int(0x2b):
        reg_dst |= 0
        branch |= 0
        reg_write |= 0
        alu_src |= 1
        mem_write |= 1
        mem_to_reg |= 0
        alu_op |= 0
    #BEQ
    with op == int(0x4):
        reg_dst |= 0
        branch |= 1
        reg_write |= 0
        alu_src |= 0
        mem_write |= 0
        mem_to_reg |= 0
        alu_op |= 5
#Register Variables
r_reg0 = pyrtl.WireVector(bitwidth=5, name = 'r_reg0')
r_reg1 = pyrtl.WireVector(bitwidth=5, name = 'r_reg1')
w_data = pyrtl.WireVector(bitwidth=32, name ='w_data')
w_reg = pyrtl.WireVector(bitwidth = 5, name ='w_reg')

#Register Logic
with pyrtl.conditional_assignment:
    with reg_dst == int(0x0):
        #Write to rt
        w_reg |= rt
    with reg_dst == int(0x1):
        #Write to rd
        w_reg |= rd
r_reg0 <<= rs
r_reg1 <<= rt
#ALU Variables
data0 = pyrtl.WireVector(bitwidth=32, name = 'data0')
data1 = pyrtl.WireVector(bitwidth=32, name = 'data1')
alu_out = pyrtl.WireVector(bitwidth=32, name = 'alu_out')
beq_check = pyrtl.WireVector(bitwidth = 1, name = 'beq_check')
pos = 0x0000
neg = 0xffff
#Evaluate ALU input values
data0 <<=  rf[r_reg0]
with pyrtl.conditional_assignment:
    #Determine Second ALU input
    with alu_src == int(0x0):
        #Read from 2nd register
        data1 |= rf[r_reg1]
    with alu_src == int(0x1):
        #Pass signed Immed
        data1 |= immed.sign_extended(32)
    with alu_src == int(0x2):
        #Pass unsigned Immed
        data1 |= immed.zero_extended(32)

#ALU Logic
with pyrtl.conditional_assignment:
    #Add Op
    with alu_op==int(0x0):
        alu_out |= data0 + data1
    #And Op
    with alu_op==int(0x1):
        alu_out |= data0 & data1
    #LUI Op
    with alu_op==int(0x2):
        shift = pyrtl.WireVector(bitwidth=5)
        shift <<= 16
        alu_out |= pyrtl.corecircuits.shift_left_logical(data1, shift)
    #ORI Op
    with alu_op==int(0x3):
        alu_out |= data0 | data1
    #SLT Op
    with alu_op==int(0x4):
        alu_out |= pyrtl.corecircuits.signed_lt(data0, data1)
    #BEQ
    with alu_op==int(0x5):
        #Get conditional
        beq_check |= data0 == data1
        #If equal execute Jump
        with beq_check==int(0x1):
            jump |= immed.sign_extended(32)
    #Set jump to 0
    with alu_op != 5:
        jump |= 0


#w_data
with pyrtl.conditional_assignment:
    #Standard Case
    with mem_to_reg==0:
        with mem_write==1:
            w_data |= rf[rt]
        with mem_write!=1:
            w_data |= alu_out
    #LW case
    with mem_to_reg==1:
        w_data |= d_mem[alu_out]

#write to mem
with pyrtl.conditional_assignment:
    #SW
    with mem_write==1:
        #alu_out holds address
        d_mem[alu_out] |= w_data
    with reg_write==1:
        with w_reg!=0:
            rf[w_reg] |= w_data
if __name__ == '__main__':

    """

    Here is how you can test your code.
    This is very similar to how the autograder will test your code too.

    1. Write a MIPS program. It can do anything as long as it tests the
       instructions you want to test.

    2. Assemble your MIPS program to convert it to machine code. Save
       this machine code to the "i_mem_init.txt" file.
       You do NOT want to use QtSPIM for this because QtSPIM sometimes
       assembles with errors. One assembler you can use is the following:

       https://alanhogan.com/asu/assembler.php

    3. Initialize your i_mem (instruction memory).

    4. Run your simulation for N cycles. Your program may run for an unknown
       number of cycles, so you may want to pick a large number for N so you
       can be sure that the program has "finished" its business logic.

    5. Test the values in the register file and memory to make sure they are
       what you expect them to be.

    6. (Optional) Debug. If your code didn't produce the values you thought
       they should, then you may want to call sim.render_trace() on a small
       number of cycles to see what's wrong. You can also inspect the memory
       and register file after every cycle if you wish.

    Some debugging tips:

        - Make sure your assembly program does what you think it does! You
          might want to run it in a simulator somewhere else (SPIM, etc)
          before debugging your PyRTL code.

        - Test incrementally. If your code doesn't work on the first try,
          test each instruction one at a time.

        - Make use of the render_trace() functionality. You can use this to
          print all named wires and registers, which is extremely helpful
          for knowing when values are wrong.

        - Test only a few cycles at a time. This way, you don't have a huge
          500 cycle trace to go through!

    """

    # Start a simulation trace
    sim_trace = pyrtl.SimulationTrace()

    # Initialize the i_mem with your instructions.
    i_mem_init = {}
    with open('i_mem_init.txt', 'r') as fin:
        i = 0
        for line in fin.readlines():
            i_mem_init[i] = int(line, 16)
            i += 1

    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
        i_mem : i_mem_init
    })

    # Run for an arbitrarily large number of cycles.
    for cycle in range(500):
        sim.step({})

    #Use render_trace() to debug if your code doesn't work.
    sim_trace.render_trace()

    # You can also print out the register file or memory like so if you want to debug:
    print(sim.inspect_mem(d_mem))
    print(sim.inspect_mem(rf))

    # Perform some sanity checks to see if your program worked correctly
    assert(sim.inspect_mem(rf)[9] == 84)
    assert(sim.inspect_mem(rf)[10] == 85)
    assert(sim.inspect_mem(rf)[11] == 0xFFFFFFAB)
    assert(sim.inspect_mem(rf)[12] == 0)
    assert(sim.inspect_mem(rf)[13] == 1)
    assert(sim.inspect_mem(rf)[14] == 0)
    assert(sim.inspect_mem(rf)[15] == 0xA0000)
    print('Passed!')
