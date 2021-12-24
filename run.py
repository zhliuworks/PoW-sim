from argparse import ArgumentParser
from math import ceil
from queue import Queue
from threading import Semaphore, Thread

from powsim import Block, Node


def parse_args():
    parser = ArgumentParser(description='PoW simulation configs')
    parser.add_argument('--num-node', '-n', type=int, default=4,
                        help='the number of distributed nodes')
    parser.add_argument('--malicious-percentage', '-p', type=float, default=0.0,
                        help='the percentage of malicious nodes conducting forking attacks')
    parser.add_argument('--hash-difficulty', '-d', type=int, default=4,
                        help='the difficulty of hash computation')
    parser.add_argument('--max-hash-times', type=int, default=100000,
                        help='the maximum times of repeated hash computation in a block')
    parser.add_argument('--max-trials-honest', type=int, default=3,
                        help='the maximum times of mine trials in an honest node')
    parser.add_argument('--max-trials-malicious', type=int, default=3,
                        help='the maximum times of mine trials in a malicious node')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    Block.hash_difficulty = args.hash_difficulty
    Block.max_hash_times = args.max_hash_times
    Node.max_trials_honest = args.max_trials_honest
    Node.max_trials_malicious = args.max_trials_malicious

    nodes = []
    consensus_locks = []
    mine_locks = []
    threads = []
    num_malicious = ceil(args.num_node * args.malicious_percentage)

    for i in range(args.num_node):
        # i < num_malicious -> malicious node
        nodes.append(Node(i, args.num_node, num_malicious))
        Node.channels[i] = Queue()
        consensus_locks.append(Semaphore(args.num_node))
        mine_locks.append(Semaphore(0))

    for i in range(args.num_node):
        threads.append(Thread(target=nodes[i].run, args=(consensus_locks, mine_locks)))
        threads[i].start()

    for i in range(args.num_node):
        threads[i].join()


if __name__ == '__main__':
    main()
