
RANGE=1000

# env_name="Asteroids"
# agent="train_HER.py"
agent="train_HER_mod.py"
offset=".04"
args='--replay-k=8 --entropy-regularization=0.05 --n-test-rollouts=10' # --n-cycles=100'
# command="mpirun -np 6 python -u train_HER_mod.py --env-name=$env_name $args"
# command="mpirun -np 6 python -u train_HER.py --env-name=$env_name $args"
#mpirun -np 6 python -u train_HER.py --env-name=FetchSlide-v1 --replay-k=8 --entropy-regularization=0.05  --two-goal --apply-ratio
# $command --seed=$(($RANDOM % $RANGE))
# args='--n-epochs=2 --n-test-rollouts=50 --n-cycles=10'
# python -u train_HER.py --env-name=Asteroids --replay-k=8 --entropy-regularization=0.05 --n-epochs=5 --n-test-rollouts=10 --n-cycles=10
for env_name in "2Dnav" #"Car" #"Asteroids" 
do
	logfile="logging/$env_name.txt"
	echo "" > $logfile
	# epochs=5
	if [ "$env_name" == "Asteroids" ]; then epochs=5 
	fi
	if [ "$env_name" == "Car" ]; then epochs=10 
	fi
	if [ "$env_name" == "2Dnav" ]; then epochs=15 
	fi
	command="python -u $agent --env-name=$env_name $args --n-epochs=$epochs --ratio-offset=$offset"
	for noise in 0 .1 .25 .5 1.0
	do 
		echo -e "\nrunning $env_name, $noise noise, 2-goal ratio with $offset offset" >> $logfile
		for i in 0 1 2 3 4
		do 
			echo "running $env_name, $noise noise, 2-goal ratio with $offset offset"
			echo "command: $command"
			$command --action-noise=$noise --seed=$(($RANDOM % $RANGE)) --two-goal --apply-ratio
		done
		echo -e "\nrunning $env_name, $noise noise, 2-goal" >> $logfile
		for i in 0 1 2 3 4
		do 
			echo "running $env_name, $noise noise, 2-goal"
			$command --action-noise=$noise --seed=$(($RANDOM % $RANGE)) --two-goal
		done
		echo -e "\nrunning $env_name, $noise noise, 1-goal" >> $logfile
		for i in 0 1 2 3 4
		do 
			echo "running $env_name, $noise noise, 1-goal"
			$command --action-noise=$noise --seed=$(($RANDOM % $RANGE))
		done
	done
done