import random
from web3 import Web3
from typing import List

# 初始化 Web3 连接
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))  # 本地区块链节点（Ganache 或 Hardhat）
contract_address = "0xYourContractAddressHere"       # 替换为智能合约地址
abi = [...]                                          # 智能合约 ABI，需预先定义
contract = w3.eth.contract(address=contract_address, abi=abi)

# 基因个体类
class Individual:
    def __init__(self, genes: List[int]):
        self.genes = genes  # 基因序列（输入数据）
        self.fitness = 0    # 适应度

    def mutate(self, mutation_rate: float):
        """随机突变基因"""
        for i in range(len(self.genes)):
            if random.random() < mutation_rate:
                self.genes[i] = random.randint(0, 255)  # 假设输入为字节数组

# 遗传算法核心
class GeneticFuzzer:
    def __init__(self, population_size: int, generations: int, mutation_rate: float):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.population = self.initialize_population()

    def initialize_population(self) -> List[Individual]:
        """随机生成初始种群"""
        return [Individual([random.randint(0, 255) for _ in range(10)]) for _ in range(self.population_size)]

    def evaluate_fitness(self, individual: Individual):
        """评估个体适应度（基于合约调用结果）"""
        try:
            result = contract.functions.targetFunction(*individual.genes).call()
            # 自定义适应度函数，例如：返回值是否异常或路径覆盖率
            individual.fitness = self.calculate_fitness(result)
        except Exception as e:
            individual.fitness = 0  # 异常作为低适应度处理

    def calculate_fitness(self, result):
        """根据目标定义适应度"""
        return len(str(result))  # 示例：结果长度为适应度

    def select_parents(self) -> List[Individual]:
        """轮盘赌选择法选择父代"""
        total_fitness = sum(ind.fitness for ind in self.population)
        pick = random.uniform(0, total_fitness)
        current = 0
        for individual in self.population:
            current += individual.fitness
            if current > pick:
                return individual

    def crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        """单点交叉"""
        crossover_point = random.randint(0, len(parent1.genes) - 1)
        child_genes = parent1.genes[:crossover_point] + parent2.genes[crossover_point:]
        return Individual(child_genes)

    def fuzz(self):
        """遗传算法主循环"""
        for generation in range(self.generations):
            print(f"Generation {generation}")
            # 评估适应度
            for individual in self.population:
                self.evaluate_fitness(individual)

            # 按适应度排序
            self.population.sort(key=lambda ind: ind.fitness, reverse=True)
            print(f"Best fitness: {self.population[0].fitness}")

            # 选择下一代
            new_population = []
            for _ in range(self.population_size // 2):
                parent1 = self.select_parents()
                parent2 = self.select_parents()
                child1 = self.crossover(parent1, parent2)
                child2 = self.crossover(parent2, parent1)
                child1.mutate(self.mutation_rate)
                child2.mutate(self.mutation_rate)
                new_population.extend([child1, child2])

            self.population = new_population

# 执行模糊测试
fuzzer = GeneticFuzzer(population_size=20, generations=50, mutation_rate=0.1)
fuzzer.fuzz()
