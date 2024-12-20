# ADSAPlace

```bash
cmake .
make
./bin/PCBPLACER KICAD_PCB(file) [options]
```
## Parameters

```bash
Options:
[1] : outer_iters 
[2] : inner_iters
[3] : initial placement mode
        default:Random placement
        1:      Center placement
        2:      Spiral placement
        3:      Greedy placement
        4:      classification placement for bench 2 and bench 9(bench has information of pcb's type)
        5:      classification placement for others' bench
        6:      analytic placement
[4] : pseudo routing
[5] : test_flow
```