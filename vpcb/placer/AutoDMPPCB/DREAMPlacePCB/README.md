# DREAMPlacePCB

Deep learning toolkit-enabled PCB placement.

# How to Update Submodules

To pull git submodules in the DREAMPlacePCB/thirdparty directory

```
cd  auto-pcb
git submodule init
git submodule update 
```

If you failed, delete the submodules directory in .gitmodules files and try the command above again.

Or alternatively, pull all the submodules when cloning the repository.

```
git clone --recursive https://github.com/WHU-RVLAB/auto-pcb.git
```

# How to Build

```
cd vpcb/placer/DREAMPlacePCB
./build.sh
```

If you can not run build.sh, try to delete CRLF in build.sh

```
sed -i "s/\r//" ./build.sh
```

To clean

```
cd vpcb/placer/DREAMPlacePCB
rm -r build
```

# How to Run

run with JSON configuration file for full placement.

```
cd vpcb
python run.py
```

Or alternatively

```
cd vpcb/placer/DREAMPlacePCB
python placer.py
```

Test individual `pytorch` op with the unit tests

```
cd vpcb/placer/DREAMPlacePCB
python ops/hpwl/hpwl_unittest.py
```
