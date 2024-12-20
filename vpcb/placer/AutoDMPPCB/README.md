# AutoDMPPCB: Automated DREAMPlacePCB-based Placement

AutoDMPPCB adds automatic parameter tuning based on multi-objective hyperparameter Bayesian optimization (MOBO).

# How to Run

To run the test of multi-objective Bayesian optimization:
```
./run_tuner.sh 1 1 ./configspace.json ./ppa.json \"\" 200 16 0 0 16 ./ ./mobohb_log
```
If you can not run run_tuner.sh, try to delete CRLF in run_tuner.sh

```
sed -i "s/\r//" ./run_tuner.sh
```
