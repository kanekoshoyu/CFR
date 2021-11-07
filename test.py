import util.test_profile as prof
import random
from typing import List, long
n = random.random()
print(n)

rock: int = 0
paper: int = 1
scissor: int = 2
num_action: int = 3

regret_sum: List[long] = []
strategy: List[long] = []
strategy_sum: List[long] = []
oppStrategy = {0.4, 0.3, 0.3}


def getStrategy():
    for i in 0..num_action:
        if regret_sum[i] > 0:
            strategy[i] = regret_sum[i]
        else:
            regret_sum[i] = 0

    for i in 0..num_action:
        if normalizingSum > 0:
            strategy[i] /= normalizingSum
        else:
            strategy[i] = float(1.0/num_action)
    return strategy


def main():
    getStrategy()


if __name__ == "__main__":
    main()


# private double[] getStrategy() {
# double normalizingSum = 0;
# for (int a = 0; a < NUM_ACTIONS; a++) {
# strategy[a] = regretSum[a] > 0 ? regretSum[a] : 0;
# normalizingSum += strategy[a];
# }
# for (int a = 0; a < NUM_ACTIONS; a++) {
# if (normalizingSum > 0)
# strategy[a] /= normalizingSum;
# else
# strategy[a] = 1.0 / NUM_ACTIONS;
# strategySum[a] += strategy[a];
# }
# return strategy;
# }
