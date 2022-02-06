import pdb
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

ci = lambda x, z=2: (np.mean(x) - z*np.std(x)/len(x)**.5, np.mean(x) + z*np.std(x)/len(x)**.5 )
err_bar = lambda x, z=2: z*np.std(x)/len(x)**.5

def parse_log(filename):
	with open(filename, "r") as f: 
		file = f.read()

	file_list = file.split("\n")
	experiment_dict = {}
	current_list = []
	for line in reversed(file_list):
		# pdb.set_trace()
		if line == '': 
			continue
		elif "run" in line: 
			env, noise_string, method = tuple(line.split(","))
			noise = float(noise_string[:-len("noise")])
			mean = np.mean(current_list)
			list_ci = ci(current_list)
			if method not in experiment_dict.keys():
				experiment_dict[method] = []
			# experiment_dict[method].append((noise, current_list))
			# if "2-goal ratio" in line:
			# 	pdb.set_trace()
			experiment_dict[method].append((noise, mean, list_ci))
			current_list = []
		else: 
			data = line.split(",")
			num = 0#float(line.split(":")[-1])
			for item in data: 
				if "success_rate" in item: 
					num = float(line.split(":")[-1])
			current_list.append(num)

	return experiment_dict

def plot_log(experiment_dict):
	color_list = ["red", "green", "blue", "brown", "pink"]
	i=0
	for method in experiment_dict.keys():
		noise_list = [elem[0] for elem in experiment_dict[method]]
		mean_list = [elem[1] for elem in experiment_dict[method]]
		upper_ci_list = [elem[2][0] for elem in experiment_dict[method]]
		lower_ci_list = [elem[2][1] for elem in experiment_dict[method]]

		plt.plot(noise_list, mean_list, color=color_list[i],label=method)
		plt.fill_between(noise_list, lower_ci_list, upper_ci_list, color=color_list[i], alpha=.1)

		i += 1

	plt.xlabel("Noise (fraction of maximum action)")
	plt.ylabel("Success Rate")
	plt.title("Asteroids Performance")
	plt.legend()
	plt.show()

	# pdb.set_trace()


if __name__ == '__main__':
	print(plot_log(parse_log("logging/Asteroids.txt")))