import random
import asyncio
import time
import datetime
import json
import hashlib

from aioconsole import ainput



class Node:

    def __init__(self, ip: str, power: int, balance: int = 0):
        self.ip = ip
        self.power = power
        self.balance = 0


class Block:

    def __init__(self, index: int, data: str, previous_hash: str):
        self.index = index
        self.timestamp = datetime.datetime.now()
        self.data = data  # фиктивные мета-данные транзакции
        self.previous_hash = previous_hash
        self.nonce = 0

    def compute_hash(self):
        block = {
            "index": self.index,
            "timestamp": str(self.timestamp),
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }
        block_encoded = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_encoded).hexdigest()


class BlockChain:

    def __init__(self):
        self.chain = [self._create_genesis_block()]  # добавляем генезиз-блок, от которого будем вычислять хеш
        self.nodes = []
        self.nodes_queue = asyncio.Queue()
        self.difficulty = 1
        self._fixed_complexity = False

    @staticmethod
    def _cancel_mining_current_block():
        tasks = asyncio.all_tasks()
        print(tasks)
        for task in tasks:
            if task == asyncio.current_task():
                pass
            else:
                task.cancel()
        pass

    @staticmethod
    def _create_genesis_block():
        return Block(0, "Genesis Block", "0")

    # Добавить подобие вилки
    async def create_fork(self):
        pass

    async def mine_block(self, node: Node, block: Block, difficulty: int = None):
        if not difficulty:
            difficulty = self.difficulty
        block.previous_hash = self.get_latest_block().compute_hash()  # вычисляем хеш нового блока по хешу предыдущего
        await self._proof_of_work(node, block, difficulty)
        self.chain.append(block)
        print("new block created")

    async def add_node(self, node: Node):
        self.nodes.append(node)
        await self.nodes_queue.put(self.nodes[-1])

    async def _proof_of_work(self, node: Node, block: Block, difficulty: int):

        start_timer = time.time()
        computed_hash = block.compute_hash()

        while not computed_hash.startswith('0' * difficulty):
            node = await self.nodes_queue.get()
            block.nonce += 1
            computed_hash = block.compute_hash()
            await self.nodes_queue.put(node)

        print(f'время вычисления: {round(time.time() - start_timer, 4)} ms')
        node.balance += 20
        self._cancel_mining_current_block()

    def show_table(self):
        print("    ip          |  Heshrate   | balance")
        for node in self.nodes:
            print(f"{node.ip}  | {node.power} HS/p |    {node.balance}")

    #
    # def turn_fixed_complex(self):
    #     # Автоматически запрещает дальнейшее усложнение вычисление сети до вызова off_fixed_complex
    #     self._fixed_complexity = True
    #
    # def off_fixed_complex(self):
    #     self._fixed_complexity = False
    #
    # def is_fixed_complex(self):
    #     return self._fixed_complexity

    def get_latest_block(self):
        return self.chain[-1]


class CmdPanel:

    def __init__(self, blockchain: BlockChain):
        self.blockchain = blockchain
        self.index = 0

    @staticmethod
    async def show_help_message(*args):
        print("commands:\nnode add -hs\nhelp\nshow book\n")

    @staticmethod
    async def show_book(*args):
        blockchain.show_table()

    async def mining_members_tasks(self):

        def get_previous_hash():
            return self.blockchain.get_latest_block().previous_hash

        def create_node(power: int = 10):
            ip = ".".join(map(str, (random.randint(0, 255)
                                    for _ in range(4))))
            return Node(ip, power)

        node = create_node()
        new_block = Block(self.index, "data", get_previous_hash())
        self.index += 1
        await self.blockchain.add_node(node)
        # if blockchain.is_fixed_complex():
        #     await asyncio.create_task(self.blockchain.mine_block(node, new_block))
        # else:
        await asyncio.create_task(self.blockchain.mine_block(node, new_block, self.index))

    async def add_new_member_in_blockchain(self, cmd: str):
        if len(cmd.split()) == 3 or len(cmd.split()) == 2:
            try:
                await self.mining_members_tasks()
            except asyncio.exceptions.CancelledError:
                pass
        else:
            print("wrong command flags")

    # async def set_difficulty_hash(self, cmd: int):
    #     if type(cmd) != int:
    #         print("Incorrent value, please enter [command] [integer]")
    #         return
    #
    #     self.blockchain.difficulty = cmd


async def main(command_panel: CmdPanel):
    commands = {"add node": command_panel.add_new_member_in_blockchain,
                "help": command_panel.show_help_message,
                "show book": command_panel.show_book,
                # "set complex": command_panel.set_difficulty_hash,
                }
    while True:
        cmd = await ainput(">>>")
        if commands.get(cmd):
            await commands.get(cmd)(cmd)
        else:
            print(f"Error command")
            await commands.get("help")()


if __name__ == "__main__":
    blockchain = BlockChain()
    panel = CmdPanel(blockchain)
    event_loop = asyncio.get_event_loop()
    asyncio.run(main(panel), debug=True)

