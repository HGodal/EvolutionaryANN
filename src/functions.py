"""
Python helper functions for training agents.

Functions:
    create_new_network - Create new MLP Classifier.
    initialise_population -  Initalises a population of agents.
    simulate_agent - Simulates the chosen agent in the environment.
    de_crossover - Differential crossover.
    mutationFunc_W_B -  Mutate both weights and biases for an agent.
    mutation_rate - Dynamic mutation rate function.
    average_weight_and_bias - Calculate the average weight and bias.
    nnPerformance - Visualize the performance from each generation.
    save_frames_as_gif - Storing gif of trained agent.

    partial_fit - Partial fitting model on experience.
    breedCrossover - Breeds a child using two point crossover.
    de_crossover_classic - Breeds a child from a classic de algorithm.
    crossoverSinglePoint - Breeds two children using one point crossover.


Functions by Author:
    Bjørn Christian Weinbach:
        create_new_network
        initialise_population
        simulate_agent
        mutation_rate
        save_frames_as_gif

    Marius Sørensen:
        create_new_network
        simulate_agent

    Ove Jørgensen:
        mutationFunc_W_B
        average_weight_and_bias

    Håvard Godal:
        simulate_agent
        de_crossover
        de_crossover_classic

    Johanna Kinstad:
        mutationFunc_W_B

    Vegard Rongve:
        mutationFunc_W_B
        nnPerformance
"""

from sklearn.neural_network import MLPClassifier
import numpy as np
import random
import copy
import matplotlib.pyplot as plt
from matplotlib import animation


def create_new_network(env):
    """[Create a new MLPCLassifier].

    Author:
        [Bjørn Christian Weinbach, Marius Sørensen]

    Args:
        env ([type]): [description]

    Returns:
        [type]: [description]
    """
    return MLPClassifier(
        batch_size=1,
        max_iter=1,
        solver='sgd',
        activation='relu',
        learning_rate='invscaling',
        hidden_layer_sizes=4,
        random_state=1
    ).partial_fit(np.array([env.observation_space.sample()]),
                  np.array([env.action_space.sample()]),
                  classes=np.arange(env.action_space.n))


def initialise_population(size, env):
    """[Initialise size number of agents].

    Author: Bjørn Christian Weinbach

    Args:
        size ([Int]): [Number of agents in population]
        env ([OpenAI Gym]): [Environment]

    Returns:
        [type]: [description]
    """
    population = []
    for _ in range(size):
        population.append(create_new_network(env))
    return population


def simulate_agent(agent, env, render=False, savetofile=False, filename=None):
    """Simulate an agent in an environment and return its fitness score.

    Author: [Håvard Godal, Marius Sørensen, Bjørn Christian Weinbach]

    Args:
        agent (MLPClassifier): [Neural Network]
        env ([OpenAI Gym]): [Environment]

    Returns:
        [score]: [Fitness score of agent]
    """
    observation = env.reset()
    score = 0
    done = False
    frames = []

    # Agent-Environment Interaction
    while not done:
        action = int(agent.predict(
            observation.reshape(1, -1)))
        observation, reward, done, _ = env.step(action)
        score += reward

        if savetofile:
            frames.append(env.render(mode="rgb_array"))
        if render:
            env.render()
    if savetofile:
        save_frames_as_gif(frames, path='./gifs/', filename=filename)

    return score


def de_crossover(nn1, nn2):
    """Create new weights and biases through a modified de-crossover.

    Author: Håvard Godal

    Args:
        nn1 (MLPClassifier): [Neural Network]
        nn2 (MLPClassifier): [Neural Network]

    Returns:
        [newcoeffs]: [Weights of new network]
        [newintercepts]: [Biases of new network]
    """
    newcoefs = []
    newintercepts = []
    for i in range(2):
        shape = nn1.coefs_[i].shape
        coef1Flat = np.ravel(nn1.coefs_[i])
        coef2Flat = np.ravel(nn2.coefs_[i])

        newcoefs.append(
            np.array(
                coef1Flat + np.random.uniform(
                    0,
                    1,
                    len(coef1Flat)
                ) * (coef2Flat-coef1Flat)
            ).reshape(shape)
        )

        shape = nn1.intercepts_[i].shape
        intercepts1Flat = np.ravel(nn1.intercepts_[i])
        intercepts2Flat = np.ravel(nn2.intercepts_[i])

        newintercepts.append(
            np.array(
                intercepts1Flat + np.random.uniform(
                    0,
                    1,
                    len(intercepts1Flat)
                ) * (intercepts2Flat-intercepts1Flat)
            ).reshape(shape)
        )
    return newcoefs, newintercepts


def mutationFunc_W_B(agent, mutation_rate, method):
    """Mutate agents weights and biases.

    Author:
        Vegard Rongve, Johanna Kinstad, Ove Jørgensen

    Args:
        agent ([MLPClassifier]): [Neural Network of agent]
        mutation_rate ([float]): [Probability of mutation]
        method ([ "swap" | "inverse" | "scramble" | "uniform" | "gaussian" ]):
            [Type of mutation operation]

    Returns:
        [agent]: [Mutated agent]
    """
    for item in range(2):
        if item == 0:
            node_item = agent.coefs_
        else:
            node_item = agent.intercepts_

        for el in node_item:
            for swappedRow in el:
                if (random.random() < mutation_rate):
                    random1 = int(random.random()*len(el))
                    random2 = int(random.random()*len(el))
                    if(random1 > random2):
                        random2, random1 = random1, random2

                    if(method == 'swap'):
                        swappedRow, el[random1] = el[random1], swappedRow

                    elif(method == 'scramble'):
                        random.shuffle(el[random1:random2])

                    elif(method == 'inverse'):
                        el[random1:random2] = el[random1:random2][::-1]

                    else:
                        if(type(swappedRow) == np.float64):
                            if method == 'gaussian':
                                swappedRow += np.random.normal(0, 2)
                            elif method == 'uniform':
                                swappedRow = random.random()
                        else:
                            for inner in swappedRow:
                                if method == 'gaussian':
                                    inner += np.random.normal(0, 2)
                                elif method == 'uniform':
                                    inner = random.random()

    return agent


def mutation_rate(score, goal):
    """Dynamic mutation rate.

    Author: Bjørn Christian Weinbach

    Algorithm:
        High mutation rate in beginning -> explores space
        When good agents are found:
            Low mutation rate so new agents are similar to
            previous ones (given that they have a high score)

    Args:
        score (float): [score of best agent]
        goal (float): [Linear function decreasing as score -> goal]

    Return:
        (float): [Mutation rate]
    """
    return(1 - (score/goal))


def average_weight_and_bias(population, env):
    """Calculate the average weight and bias from a given population.

    Author: Ove Jørgensen

    Args:
        population: The population from which to calculate
        env: OpenAI Gym environment.

    Returns:
        [avg_network]: A new network given the average bias and weight
    """
    def find_mean(mat, attr_type, i): return np.mean(
        np.array([getattr(el, attr_type)[i] for el in mat]),
        axis=0
    )
    coef0 = find_mean(population, 'coefs_', 0)
    coef1 = find_mean(population, 'coefs_', 1)
    intercept0 = find_mean(population, 'intercepts_', 0)
    intercept1 = find_mean(population, 'intercepts_', 1)

    avg_network = create_new_network(env)
    avg_network.coefs_ = [coef0, coef1]
    avg_network.intercepts_ = [intercept0, intercept1]

    return avg_network


def nnPerformance(generation, best_score, average_score, acceptanceCriteria):
    """Visualize the performance from each generation.

    Author: Vegard Rongve

    Args:
        generation: generation size
        best_score: list with best scores from each generation
        average_score: list with average scores from each generation
        acceptanceCriteria: Horisontal line of acceptance ratio.

    Returns:Plot
    """
    plt.plot(range(generation), best_score, label="Max score")
    plt.plot(range(generation), average_score, label="Average score")
    plt.title('Fitness through the generations')
    plt.axhline(y=acceptanceCriteria, color='r',
                linestyle='--', label="Acceptance ratio")
    plt.legend()
    plt.xlabel("Generations")
    plt.ylabel("Fitness")
    plt.show()


def save_frames_as_gif(frames, path='./', filename='gym_animation.gif'):
    """Save environment render as gif.

    "Stolen" from github user botforge. Modified to make it compatible.
    url: https://gist.github.com/botforge/64cbb71780e6208172bbf03cd9293553

    Author: Github: botforge, Modified Bjørn Christian Weinbach

    Args:
        frames (List): [List of env.render(mode="rgb_array")]
        path (str, optional): [Filepath]. Defaults to './'.
        filename (str, optional): [Filename of gif].
    """
    # Mess with this to change frame size
    plt.figure(figsize=(frames[0].shape[1] / 72.0,
                        frames[0].shape[0] / 72.0), dpi=72)

    patch = plt.imshow(frames[0])
    plt.axis('off')

    def animate(i):
        patch.set_data(frames[i])

    anim = animation.FuncAnimation(
        plt.gcf(), animate, frames=len(frames), interval=50)

    anim.save(path + filename, writer='pillow', fps=60)


def de_crossover_classic(agent, randomAgents):
    """Create new weights and biases through a de-crossover.

    Author: Håvard Godal

    Args:
        agent (MLPClassifier): [Neural Network]
        randomAgents (List) : [List of MLPClassifiers]

    Returns:
        [newcoeffs]: [Weights of new network]
        [newintercepts]: [Biases of new network]
    """
    # Crossover probability
    CR = 0.9
    # Differential weight
    F = 0.8

    newcoefs = []
    newintercepts = []
    for i in range(2):
        shape = agent.coefs_[i].shape
        R = np.random.random_integers(0, len(agent.coefs_[i]))

        agentCoefFlat = np.ravel(agent.coefs_[i])
        coef1Flat = np.ravel(randomAgents[0].coefs_[i])
        coef2Flat = np.ravel(randomAgents[1].coefs_[i])
        coef3Flat = np.ravel(randomAgents[2].coefs_[i])

        for j in range(len(agentCoefFlat)):
            r = np.random.uniform()

            if r < CR or j == R:
                agentCoefFlat[j] = coef1Flat[j] + \
                    F * (coef2Flat[j] - coef3Flat[j])

        newcoefs.append(agentCoefFlat.reshape(shape))

        shape = agent.intercepts_[i].shape
        R = np.random.random_integers(0, len(agent.intercepts_[i]))

        agentInterceptsFlat = np.ravel(agent.intercepts_[i])
        inter1Flat = np.ravel(randomAgents[0].intercepts_[i])
        inter2Flat = np.ravel(randomAgents[1].intercepts_[i])
        inter3Flat = np.ravel(randomAgents[2].intercepts_[i])

        for j in range(len(agentInterceptsFlat)):
            r = np.random.uniform()

            if r < CR or j == R:
                agentInterceptsFlat[j] = inter1Flat[j] + \
                    F*(inter2Flat[j] - inter3Flat[j])

        newintercepts.append(agentInterceptsFlat.reshape(shape))

    return newcoefs, newintercepts
