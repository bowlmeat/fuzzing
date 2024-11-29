import random
from web3 import Web3
from typing import List, Dict, Any

# 初始化 Web3 和智能合约
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
instrumented_contract_address = "0xYourInstrumentedContractAddress"
abi = [...]  # 智能合约 ABI
contract = w3.eth.contract(address=instrumented_contract_address, abi=abi)

# 模拟 Instrumented EVM 的反馈接口
class TaintAnalysisInstrumentedEVM:
    def __init__(self, contract):
        self.contract = contract

    def execute_with_taint_feedback(self, tx_sequence: List[Dict[str, Any]]) -> Dict:
        """
        执行交易序列并返回污点分析信息
        """
        try:
            taint_feedback = []
            for tx in tx_sequence:
                txn = self.contract.functions[tx['function']](*tx['inputs']).transact({"from": tx['from']})
                receipt = w3.eth.get_transaction_receipt(txn)
                # 模拟返回的污点反馈信息
                feedback = {
                    "execution_trace": receipt["logs"],  # 执行轨迹
                    "tainted_variables": [0, 2],  # 假设变量索引 0 和 2 被标记为污点
                    "data_flow": [("x", "balance"), ("y", "withdrawAmount")],  # 数据流
                    "success": True
                }
                taint_feedback.append(feedback)
            return {"taint_feedback": taint_feedback, "success": True}
        except Exception as e:
            return {"taint_feedback": [], "success": False}

# 污点分析辅助的遗传算法 Fuzzing 框架
class TaintGuidedFuzzer:
    def __init__(self, instrumented_evm: TaintAnalysisInstrumentedEVM, population_size: int, generations: int, mutation_rate: float):
        self.instrumented_evm = instrumented_evm
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.population = self.initialize_population()

    def initialize_population(self) -> List[List[Dict]]:
        """随机生成初始种群（交易序列）"""
        return [
            [{"function": "deposit", "inputs": [random.randint(1, 100)], "from": w3.eth.accounts[0]},
             {"function": "withdraw", "inputs": [random.randint(1, 50)], "from": w3.eth.accounts[0]}]
            for _ in range(self.population_size)
        ]

    def evaluate_fitness(self, tx_sequence: List[Dict]) -> int:
        """基于污点分析信息评估适应度"""
        feedback = self.instrumented_evm.execute_with_taint_feedback(tx_sequence)
        if feedback["success"]:
            taint_score = sum(len(tx["tainted_variables"]) for tx in feedback["taint_feedback"])
            return taint_score  # 使用污点变量数量作为适应度
        else:
            return 0

    def mutate(self, tx_sequence: List[Dict], taint_feedback: List[Dict]) -> List[Dict]:
        """基于污点信息进行突变"""
        for i, tx in enumerate(tx_sequence):
            if random.random() < self.mutation_rate:
                # 如果当前交易的变量被标记为污点，则优先突变其输入
                if len(taint_feedback[i]["tainted_variables"]) > 0:
                    tx["inputs"][0] += random.randint(-10, 10)  # 修改被污点标记的变量
                else:
                    tx["inputs"][0] = random.randint(0, 100)
        return tx_sequence

    def crossover(self, parent1: List[Dict], parent2: List[Dict]) -> List[Dict]:
        """单点交叉生成新交易序列"""
        crossover_point = random.randint(0, len(parent1) - 1)
        return parent1[:crossover_point] + parent2[crossover_point:]

    def fuzz(self):
        """主循环"""
        for generation in range(self.generations):
            print(f"Generation {generation}")
            fitness_scores = []

            # 评估适应度
            for tx_sequence in self.population:
                feedback = self.instrumented_evm.execute_with_taint_feedback(tx_sequence)
                fitness_scores.append(self.evaluate_fitness(tx_sequence))

            # 按适应度选择最优个体
            ranked_population = sorted(zip(self.population, fitness_scores), key=lambda x: x[1], reverse=True)
            print(f"Best fitness in generation {generation}: {ranked_population[0][1]}")

            # 选择下一代（基于污点反馈优化突变）
            new_population = []
            while len(new_population) < self.population_size:
                parent1, parent2 = random.choices(ranked_population[:self.population_size // 2], k=2)
                child = self.crossover(parent1[0], parent2[0])
                feedback = self.instrumented_evm.execute_with_taint_feedback(child)
                child = self.mutate(child, feedback["taint_feedback"])
                new_population.append(child)

            self.population = new_population

# 实例化并运行
instrumented_evm = TaintAnalysisInstrumentedEVM(contract)
fuzzer = TaintGuidedFuzzer(instrumented_evm=instrumented_evm, population_size=10, generations=20, mutation_rate=0.3)
fuzzer.fuzz()
