from OpenGL.GL import *
import pickle
# from .geometric import Set
from ..spaces.objectives import TimeObjectiveFunction, TimeLengthObjectiveFunction
# from ..spaces.controlspace import LambdaKinodynamicSpace, GymWrapperControlSpace
# from ..spaces.configurationspace import MultiConfigurationSpace, BoxConfigurationSpace
from ..spaces.gymwrappers import GymWrapperGoalConditionedControlSpace, RLAgentControlSelector, DDPGAgentWrapper
from ..spaces.gymwrappers import HeuristicWrapper, GDValueSampler
from ..spaces.sets import *#
# from ..spaces.configurationspace import *
# from ..spaces.so2space import SO2Space, so2
from ..spaces.biassets import BoxBiasSet
from ..planners.problem import PlanningProblem

# from ..HER_mod.rl_modules.velocity_env import *
# from HER_mod.rl_modules.velocity_env import *
import math
# from pomp.example_problems.robotics.hand.reach import HandReachEnv
# from pomp.example_problems.robotics.hand.push import HandPushEnv
# from pomp.example_problems.robotics.hand.slide import HandSlideEnv
# from pomp.example_problems.robotics.hand.pick_and_place import HandPickAndPlaceEnv

from pomp.example_problems.robotics.hand.reach import HandReachEnv

from train_distance_function import net
import torch

"""
Left to implement: 
    Sample from goal set
    Goal set dimension (Must be same as space?)
    contains
    Project
    Signed distance
    Signed distance gradient

Tentative approach
    Treat goal loc as point in relevant dimensions, or neighborhood set
        If goal dim less than state dim, use complex space

    Sample from goal set
        Return goal loc or neighborhood sample, 
        extra dimensions are sampled from state space
    Goal set dimension (Must be same as space?)
        State space dimensions
    contains
        reward == 0
    Project
        goal pos for goal dims, point pos for non-goal-dims
    Signed distance
        distance in goal dims
    Signed distance gradient
        (pos[:goal_dims] - goal)
"""


# use_agent = False
# use_heuristic = False
use_agent = True
use_heuristic = True
use_value_function = True
# use_value_function = False
# p_goal = .5
# p_random = 0
# p_random = .5
# p_goal = 1
# p_random = .3
# p_goal = .4
p_random = .4
p_goal = .6
mean_GD_steps = 5
epsilon = 1/(1+mean_GD_steps)
# agent_loc = "saved_models/her_mod_"
agent_loc = "saved_models/her_"

# heuristic_suffix = "_distance.pkl"
goal_suffix = ".pkl"
p2p_suffix = "_p2p.pkl"

heuristic_infix = "_distance"
value_function_infix = "_value"
# agent_suffix = "_p2p.pkl"



def set_state_general(self, state: list, goal_length: int):
    assert type(state) == np.ndarray
    env_state = np.concatenate([np.array([0]),state[:-goal_length]])
    # assert type(state) == list
    # env_state = [0] + state[:-goal_length]
    self.sim.set_state_from_flattened(np.array(env_state))
    self.sim.forward()

# def state_to_goal(self, state):
#     self.sim.set_state_from_flattened(np.array(state))
#     self.sim.forward()
#     obs = self._get_obs()
#     return obs['achieved_goal']

class HandRobot: 
    def setup(self):
        obs = self.env.reset()
        self.start_state = obs['observation']#.tolist()
        self.goal = obs['desired_goal'].tolist()
        goal_length = len(self.goal)
        set_state = lambda env, state: set_state_general(env, state, goal_length)
        setattr(self.env, 'set_state', set_state)
        self.control_space = GymWrapperGoalConditionedControlSpace(self.env, self.goal)

    def controlSpace(self):
        return self.control_space

    def controlSet(self):
        return self.control_space.action_set

    def startState(self):
        return self.start_state.tolist()

    def configurationSpace(self):
        return self.control_space.configuration_space
        # res =  MultiConfigurationSpace(SO2Space(),BoxConfigurationSpace([self.omega_min],[self.omega_max]))
        #res.setDistanceWeights([1.0/(2*math.pi),1.0/(self.omega_max-self.omega_min)])
        # return res
    
    def goalSet(self):
        return self.control_space.goal_set

    def set_control_selector(self, agent_name):
        if use_agent: 
            pure_rl_agent = DDPGAgentWrapper(agent_loc + agent_name + goal_suffix, goal_conditioned=True, deterministic=True)
            agent = DDPGAgentWrapper(agent_loc + agent_name + goal_suffix, goal_conditioned=True)
            # p2p_agent = DDPGAgentWrapper(agent_loc + agent_name + p2p_suffix, goal_conditioned=True)
            p2p_agent = None
            def pure_rl_selector(controlSpace,metric,numSamples):
                return RLAgentControlSelector(controlSpace,metric,numSamples, rl_agent = pure_rl_agent,
                    p_goal = 1, p_random=0, goal=self.goal)

            def control_selector_maker(p_goal, p_random):
                rv = lambda controlSpace,metric,numSamples: RLAgentControlSelector(controlSpace,metric,numSamples, 
                    rl_agent = agent, p2p_agent=p2p_agent, p_goal = p_goal, p_random=p_random, goal=self.goal)
                return rv
    

            self.control_space.controlSelector = control_selector_maker(p_goal, 1-p_goal)
            self.control_space.p2pControlSelector = control_selector_maker(0, 0)
            self.control_space.prlcontrolSelector = control_selector_maker(p_goal, p_random)
            self.control_space.pure_rl_controlSelector = pure_rl_selector#control_selector_maker(1, 0)

            # self.control_space.controlSelector = make_control_selector
            # self.control_space.p2pControlSelector = p2p_make_control_selector


    def set_heuristic(self, heuristic_name):
        if use_heuristic: 
            heuristic = HeuristicWrapper(agent_loc + heuristic_name + heuristic_infix + p2p_suffix, self.goal, goal_conditioned=True)
            # def make_control_selector(controlSpace,metric,numSamples):
            #     return lambda x: heuristic.evaluate(x, self.goal)
                # return RLAgentControlSelector(controlSpace,metric,numSamples, rl_agent = agent, p_goal = 0, p_random=1, goal=goal)
            self.control_space.heuristic = heuristic

    def set_value_function(self, value_function_name):
        if use_value_function: 
            cs = self.configurationSpace()
            goal_filename = agent_loc + value_function_name + value_function_infix + goal_suffix
            with open(goal_filename, 'rb') as f:
                goal_value = pickle.load(f)
            # p2p_filename = agent_loc + value_function_name + value_function_infix + p2p_suffix
            # with open(p2p_filename, 'rb') as f:
            #     p2p_value = pickle.load(f)
            p2p_value = lambda x: 0

            start_state = self.start_state
            goal = self.goal

            # value = lambda x: goal_value(x) + p2p_value(x)**.5
            # gd_sampler = GDValueSampler(cs, goal_value, start_state, goal, epsilon=epsilon)
            gd_sampler = GDValueSampler(cs, goal_value, p2p_value, start_state, goal, epsilon=epsilon, 
                norm=goal_value.actor._get_norms, denorm=goal_value.actor._get_denorms)


            def normed_sample():
                samp = torch.tensor(np.random.randn(start_state.shape[0]))#*2
                return goal_value.actor._get_denorms(samp, torch.tensor(goal))[0].tolist()

            # setattr(self.control_space.configuration_space, 'distance', dist)
            setattr(self.control_space.configuration_space, 'sample', normed_sample)
            # gd_sampler = GDValueSampler(cs, value, start_state, goal, epsilon=epsilon)
            # self.control_space.configuration_space = gd_sampler
            self.control_space.configuration_sampler = gd_sampler



class HandReach(HandRobot): 
    def __init__(self):
        self.env = HandReachEnv()
        agent_name = "HandReach"
        self.env_name = agent_name
        self.setup()
        self.set_control_selector(agent_name)
        self.set_heuristic(agent_name)
        self.set_value_function(agent_name)


# def hand_reach_test():
#     print("Testing gym pendulum")
#     p = Momentum()
#     configurationspace = p.configurationSpace()
#     assert len(configurationspace.sample()) == 4
#     assert configurationspace.contains([0,0,0,0])

#     controlset = p.controlSet()
#     assert len(controlset.sample()) == 3
#     assert controlset.contains([1,0,0])


def handReachTest():
    # gym_momentum_test()
    p = HandReach()
    # objective = TimeObjectiveFunction()
    objective = TimeLengthObjectiveFunction()
    controlSpace = p.controlSpace()
    startState = p.startState()
    goalSet = p.goalSet()
    return PlanningProblem(controlSpace, startState, goalSet,
                           objective=objective)

