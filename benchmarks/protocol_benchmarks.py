"""
SuperStandard v1.0 - Protocol Performance Benchmarks

Measures performance metrics for all 3 protocols:
- ANP: Agent registration, discovery, heartbeat latency
- ACP: Coordination creation, task assignment, completion time
- BAP: Wallet operations, NFT minting, transaction processing

Usage:
    python benchmarks/protocol_benchmarks.py
"""

import asyncio
import time
import statistics
from decimal import Decimal
from typing import List, Dict, Any
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.protocols.anp_implementation import (
    AgentNetworkRegistry,
    ANPRegistration,
    DiscoveryQuery,
    AgentStatus,
)
from src.superstandard.protocols.acp_implementation import CoordinationManager
from agents.consolidated.py.blockchain_agentic_protocol import (
    BlockchainAgenticProtocol,
    AgentWallet,
    TokenType,
)


class BenchmarkResult:
    """Container for benchmark results"""

    def __init__(self, name: str):
        self.name = name
        self.times: List[float] = []
        self.errors = 0

    def add_time(self, duration: float):
        self.times.append(duration)

    def add_error(self):
        self.errors += 1

    @property
    def avg_time(self) -> float:
        return statistics.mean(self.times) if self.times else 0.0

    @property
    def min_time(self) -> float:
        return min(self.times) if self.times else 0.0

    @property
    def max_time(self) -> float:
        return max(self.times) if self.times else 0.0

    @property
    def median_time(self) -> float:
        return statistics.median(self.times) if self.times else 0.0

    @property
    def stdev_time(self) -> float:
        return statistics.stdev(self.times) if len(self.times) > 1 else 0.0

    def print_summary(self):
        print(f"\n  {self.name}:")
        print(f"    Runs: {len(self.times)}")
        print(f"    Avg: {self.avg_time*1000:.2f}ms")
        print(f"    Min: {self.min_time*1000:.2f}ms")
        print(f"    Max: {self.max_time*1000:.2f}ms")
        print(f"    Median: {self.median_time*1000:.2f}ms")
        print(f"    StdDev: {self.stdev_time*1000:.2f}ms")
        if self.errors > 0:
            print(f"    Errors: {self.errors}")


class ProtocolBenchmarks:
    """Main benchmark suite"""

    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.results: Dict[str, BenchmarkResult] = {}

    def benchmark(self, name: str):
        """Decorator for benchmarking functions"""
        if name not in self.results:
            self.results[name] = BenchmarkResult(name)
        return self.results[name]

    async def run_all(self):
        """Run all benchmarks"""
        print("\n" + "=" * 80)
        print("SuperStandard v1.0 - Protocol Performance Benchmarks")
        print("=" * 80)
        print(f"\nRunning {self.iterations} iterations per test...\n")

        await self.benchmark_anp()
        await self.benchmark_acp()
        await self.benchmark_bap()

        self.print_results()

    async def benchmark_anp(self):
        """Benchmark ANP (Agent Network Protocol)"""
        print("[ANP] Benchmarking Agent Network Protocol...")

        registry = AgentNetworkRegistry(heartbeat_timeout=300)

        # Benchmark: Agent Registration
        result = self.benchmark("ANP: Agent Registration")
        for i in range(self.iterations):
            try:
                start = time.perf_counter()
                registration = ANPRegistration(
                    agent_id=f"agent-{i}",
                    agent_type="test",
                    capabilities=["capability1", "capability2"],
                    endpoints={"api": f"http://localhost:800{i}"},
                )
                await registry.register_agent(registration)
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        # Benchmark: Agent Discovery (with agents registered)
        result = self.benchmark("ANP: Agent Discovery")
        for i in range(self.iterations):
            try:
                start = time.perf_counter()
                query = DiscoveryQuery(capabilities=["capability1"])
                await registry.discover_agents(query)
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        # Benchmark: Heartbeat
        result = self.benchmark("ANP: Heartbeat")
        for i in range(self.iterations):
            try:
                start = time.perf_counter()
                await registry.heartbeat(f"agent-{i % 10}", AgentStatus.HEALTHY, 0.5)
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        # Benchmark: Network Topology
        result = self.benchmark("ANP: Get Network Topology")
        for i in range(self.iterations):
            try:
                start = time.perf_counter()
                await registry.get_network_topology()
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        print(f"  Completed {self.iterations * 4} ANP operations")

    async def benchmark_acp(self):
        """Benchmark ACP (Agent Coordination Protocol)"""
        print("[ACP] Benchmarking Agent Coordination Protocol...")

        manager = CoordinationManager()

        # Benchmark: Coordination Creation
        result = self.benchmark("ACP: Create Coordination")
        coord_ids = []
        for i in range(self.iterations):
            try:
                start = time.perf_counter()
                coord = await manager.create_coordination(
                    coordinator_id=f"coordinator-{i}",
                    coordination_type="pipeline",
                    goal=f"Test goal {i}",
                )
                coord_ids.append(coord["coordination_id"])
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        # Benchmark: Agent Join
        result = self.benchmark("ACP: Agent Join Coordination")
        for i in range(min(self.iterations, len(coord_ids))):
            try:
                start = time.perf_counter()
                await manager.join_coordination(
                    coord_ids[i], f"agent-{i}", "worker", ["capability1"], "contributor"
                )
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        # Benchmark: Task Creation
        result = self.benchmark("ACP: Create Task")
        task_ids = []
        for i in range(min(self.iterations, len(coord_ids))):
            try:
                start = time.perf_counter()
                task = await manager.create_task(
                    coordination_id=coord_ids[i],
                    task_type="test",
                    description=f"Test task {i}",
                    priority=1,
                    input_data={},
                    dependencies=[],
                )
                task_ids.append((coord_ids[i], task["task_id"]))
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        # Benchmark: Task Assignment
        result = self.benchmark("ACP: Assign Task")
        for i in range(min(self.iterations, len(task_ids))):
            try:
                coord_id, task_id = task_ids[i]
                start = time.perf_counter()
                await manager.assign_task(coord_id, task_id, f"agent-{i}")
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        # Benchmark: Task Status Update
        result = self.benchmark("ACP: Update Task Status")
        for i in range(min(self.iterations, len(task_ids))):
            try:
                coord_id, task_id = task_ids[i]
                start = time.perf_counter()
                await manager.update_task_status(
                    coord_id, task_id, "completed", output_data={"result": "success"}
                )
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        # Benchmark: Get Progress
        result = self.benchmark("ACP: Get Progress")
        for i in range(min(self.iterations, len(coord_ids))):
            try:
                start = time.perf_counter()
                await manager.get_progress(coord_ids[i])
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        print(f"  Completed {self.iterations * 6} ACP operations")

    async def benchmark_bap(self):
        """Benchmark BAP (Blockchain Agent Protocol)"""
        print("[BAP] Benchmarking Blockchain Agent Protocol...")

        bap = BlockchainAgenticProtocol(config={})

        # Benchmark: Wallet Creation
        result = self.benchmark("BAP: Create Wallet")
        for i in range(self.iterations):
            try:
                start = time.perf_counter()
                wallet = AgentWallet(
                    wallet_id=f"wallet-{i}",
                    agent_id=f"agent-{i}",
                    public_key=f"pub_key_{i}",
                    private_key_hash=f"hash_{i}",
                    token_balances={
                        TokenType.REPUTATION: Decimal("100.0"),
                        TokenType.UTILITY: Decimal("1000.0"),
                        TokenType.GOVERNANCE: Decimal("50.0"),
                    },
                )
                await bap.wallet_manager.store_wallet(wallet)
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        # Benchmark: Get Wallet
        result = self.benchmark("BAP: Get Wallet")
        for i in range(self.iterations):
            try:
                start = time.perf_counter()
                await bap.wallet_manager.get_wallet(f"agent-{i}")
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        # Benchmark: NFT Minting
        result = self.benchmark("BAP: Mint NFT")
        for i in range(self.iterations):
            try:
                start = time.perf_counter()
                await bap.mint_capability_nft(
                    agent_id=f"agent-{i}",
                    capability_spec={
                        "name": f"capability_{i}",
                        "category": "test",
                        "proficiency_level": 0.90,
                        "description": f"Test capability {i}",
                        "authority": "Benchmark Suite",
                    },
                )
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        # Benchmark: Wallet Update
        result = self.benchmark("BAP: Update Wallet Balance")
        for i in range(self.iterations):
            try:
                wallet = await bap.wallet_manager.get_wallet(f"agent-{i}")
                start = time.perf_counter()
                wallet.token_balances[TokenType.UTILITY] += Decimal("100.0")
                await bap.wallet_manager.update_wallet(wallet)
                result.add_time(time.perf_counter() - start)
            except Exception as e:
                result.add_error()

        print(f"  Completed {self.iterations * 4} BAP operations")

    def print_results(self):
        """Print comprehensive benchmark results"""
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)

        # ANP Results
        print("\n[ANP] Agent Network Protocol Performance:")
        for key in sorted(self.results.keys()):
            if key.startswith("ANP:"):
                self.results[key].print_summary()

        # ACP Results
        print("\n[ACP] Agent Coordination Protocol Performance:")
        for key in sorted(self.results.keys()):
            if key.startswith("ACP:"):
                self.results[key].print_summary()

        # BAP Results
        print("\n[BAP] Blockchain Agent Protocol Performance:")
        for key in sorted(self.results.keys()):
            if key.startswith("BAP:"):
                self.results[key].print_summary()

        # Overall Statistics
        print("\n" + "=" * 80)
        print("OVERALL STATISTICS")
        print("=" * 80)

        total_operations = sum(len(r.times) for r in self.results.values())
        total_errors = sum(r.errors for r in self.results.values())
        avg_latency = statistics.mean([r.avg_time for r in self.results.values()])

        print(f"\nTotal operations: {total_operations}")
        print(f"Total errors: {total_errors}")
        print(f"Success rate: {(total_operations-total_errors)/total_operations*100:.2f}%")
        print(f"Average latency: {avg_latency*1000:.2f}ms")

        # Fastest operations
        print("\nTop 5 Fastest Operations:")
        sorted_by_speed = sorted(self.results.items(), key=lambda x: x[1].avg_time)
        for name, result in sorted_by_speed[:5]:
            print(f"  {name}: {result.avg_time*1000:.2f}ms")

        # Slowest operations
        print("\nTop 5 Slowest Operations:")
        for name, result in sorted_by_speed[-5:]:
            print(f"  {name}: {result.avg_time*1000:.2f}ms")

        print("\n" + "=" * 80)


async def main():
    """Run benchmark suite"""
    benchmarks = ProtocolBenchmarks(iterations=100)
    await benchmarks.run_all()

    print("\nBenchmark suite completed successfully!")
    print("\nNote: These benchmarks measure in-memory performance.")
    print("Production performance will vary based on network, storage, and load.")


if __name__ == "__main__":
    asyncio.run(main())
