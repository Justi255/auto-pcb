gpu=${1}
multiobj=${2}
cfg=${3}
base_ppa=${4}
reuse_params=${5}
iterations=${6}
workers=${7}
r_ratio=${8}
o_ratio=${9}
m_points=${10}
script_dir=${11}
log_dir=${12}

ps -fA | grep tuner_train | awk '{print $2}' | xargs kill -9 $1

# launch master process
python $script_dir/tuner_train.py --multiobj $multiobj --cfgSearchFile $cfg --n_workers $workers --n_iterations $iterations --min_points_in_model $m_points --log_dir $log_dir&

# launch worker processes
for i in $(seq $workers); do
    python $script_dir/tuner_train.py --multiobj $multiobj --log_dir $log_dir --worker --worker_id $i --run_args gpu=$gpu base_ppa=$base_ppa reuse_params=$reuse_params --route_utilization_ratio $r_ratio --overflow_ratio $o_ratio&
done
