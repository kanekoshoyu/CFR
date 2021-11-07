from enum import Enum
import numpy as np


class Node(object):
    u: float = 0.0
    p_player: float = 0.0
    p_opponent: float = 0.0

    def __init__(self, total_actions):
        self.regret_sum = np.zeros(total_actions)
        self.strategy = np.zeros(total_actions)
        self.strategy_sum = np.zeros(total_actions)

    def get_strategy(self):
        self.strategy = np.maximum(self.regret_sum, 0.0)
        norm_sum = np.sum(self.strategy)
        if norm_sum > 0:
            self.strategy /= norm_sum
        else:
            self.strategy.fill(1.0/len(self.strategy))
        self.strategy_sum += self.p_player * self.strategy
        return self.strategy

    def get_average_strategy(self):
        norm_sum = np.sum(self.strategy_sum)
        if norm_sum > 0:
            self.strategy_sum /= norm_sum
        else:
            self.strategy_sum = 1.0/len(self.strategy_sum)
        return self.strategy_sum


class Action(Enum):
    Doubt = 0
    Accept = 1


class LiarDieTrainer:
    def __init__(self, sides):
        self.sides = sides
        self.r_nodes = np.empty((sides, sides+1), dtype=Node)
        self.c_nodes = np.empty((sides, sides+1), dtype=Node)
        # Fill Response Nodes
        for my_claim in range(sides):
            for opp_claim in range(my_claim+1, sides+1):
                if opp_claim == 0 or opp_claim == sides:
                    self.r_nodes[my_claim, opp_claim] = Node(1)
                else:
                    self.r_nodes[my_claim, opp_claim] = Node(2)
        # Fill Claim Nodes
        for opp_claim in range(sides):
            for roll in range(1, sides+1):
                self.c_nodes[opp_claim, roll] = Node(sides - opp_claim)

    def initialise_rolls(self, rolls):
        for i in range(len(rolls)):
            rolls[i] = np.random.randint(self.sides) + 1
        self.c_nodes[0, rolls[0]].p_player = 1
        self.c_nodes[0, rolls[0]].p_opponent = 1

    def set_response_forward(self, rolls, opp_claim: int):
        for player_claim in range(opp_claim):
            r_node = self.r_nodes[player_claim, opp_claim]
            p_action = r_node.get_strategy()
            if opp_claim < self.sides:
                next_node = self.c_nodes[opp_claim, rolls[opp_claim]]
                next_node.p_player += (p_action[1] * r_node.p_player)
                next_node.p_opponent += r_node.p_opponent

    def set_claim_forward(self, rolls, opp_claim: int):
        c_node = self.c_nodes[opp_claim, rolls[opp_claim]]
        p_action = c_node.get_strategy()

        for player_claim in range(opp_claim+1, self.sides+1):
            p_next_claim = p_action[player_claim - opp_claim - 1]
            if p_next_claim > 0:
                next_node = self.r_nodes[opp_claim, player_claim]
                next_node.p_player += c_node.p_opponent
                next_node.p_opponent += p_next_claim * c_node.p_player

    def set_claim_backward(self, rolls, regret, opp_claim: int):
        node = self.c_nodes[opp_claim, rolls[opp_claim]]
        p_action = node.strategy
        node.u = 0.0

        for player_claim in range(opp_claim+1, self.sides+1):
            index_action = player_claim - opp_claim - 1
            next_node = self.r_nodes[opp_claim, player_claim]

            u_child = - next_node.u
            regret[index_action] = u_child
            node.u += p_action[index_action] * u_child
        for a in range(len(p_action)):
            regret[a] -= node.u
            node.regret_sum[a] += node.p_opponent * regret[a]
        node.p_player = 0
        node.p_opponent = 0

    def set_response_backward(self, rolls, regret,  opp_claim: int):
        for myClaim in range(opp_claim):
            node = self.r_nodes[myClaim, opp_claim]
            p_action = node.strategy
            node.u = 0.0
            if opp_claim > rolls[myClaim]:
                doubtUtil = 1
            else:
                doubtUtil = -1
            regret[Action.Doubt.value] = doubtUtil
            node.u += p_action[Action.Doubt.value] * doubtUtil
            if opp_claim < self.sides:
                nextNode = self.c_nodes[opp_claim, rolls[opp_claim]]
                regret[Action.Accept.value] += nextNode.u
                node.u += (p_action[Action.Accept.value] * nextNode.u)
            for a in range(len(p_action)):
                regret[a] -= node.u
                node.regret_sum[a] += (node.p_opponent * regret[a])
                node.p_player = 0
                node.p_opponent = 0

    def train(self, total_iteration):
        rolls_after_accept = np.zeros(self.sides, dtype=int)
        regret = np.zeros(self.sides)
        # print('training start')
        for i in range(total_iteration):
            self.initialise_rolls(rolls_after_accept)
            # Accumulate Realisation Weight Forward
            for opp_claim in range(self.sides+1):
                if opp_claim > 0:
                    self.set_response_forward(rolls_after_accept, opp_claim)
                if opp_claim < self.sides:
                    self.set_claim_forward(rolls_after_accept, opp_claim)
            # Back Propagation
            for opp_claim in reversed(range(self.sides+1)):
                if opp_claim < self.sides:
                    self.set_claim_backward(
                        rolls_after_accept, regret, opp_claim)
                if opp_claim > 0:
                    self.set_response_backward(
                        rolls_after_accept, regret, opp_claim)
            # Reset Strategy Sum after half the training
            if i == (total_iteration / 2):
                self.reset_strategy_sum()
        # print('training done')
        self.print_result()

    def reset_strategy_sum(self):
        for nodes in self.r_nodes:
            for node in nodes:
                if node is not None:
                    node.strategy_sum = 0
        for nodes in self.c_nodes:
            for node in nodes:
                if node is not None:
                    node.strategy_sum = 0

    def print_result(self):
        for initialRoll in range(1, self.sides+1):
            print('Initial claim policy with roll %d: %s' % (initialRoll, np.round(
                self.c_nodes[0, initialRoll].get_average_strategy(), 2)))
        print('\nOld Claim\tNew Claim\tAction Probabilities')
        for myClaim in range(self.sides):
            for oppClaim in range(myClaim+1, self.sides+1):
                print('\t%d\t%d\t%s' % (myClaim, oppClaim,
                      self.r_nodes[myClaim, oppClaim].get_average_strategy()))
        print('\nOld Claim\tRoll\tAction Probabilities')
        for oppClaim in range(self.sides):
            for roll in range(1, self.sides+1):
                print('%d\t%d\t%s' % (oppClaim, roll,
                      self.c_nodes[oppClaim, roll].get_average_strategy()))


def main():
    trainer = LiarDieTrainer(6)
    trainer.train(10000)


if __name__ == '__main__':
    main()
