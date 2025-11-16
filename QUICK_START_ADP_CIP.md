# Quick Start Guide: ADP v1.0 & CIP v1.0

## 5-Minute Quick Start

### Agent DNA Protocol (ADP) - Evolve Your Agents

```python
from src.superstandard.protocols.adp_v1 import (
    Gene, Chromosome, AgentGenome,
    GeneType, ChromosomeType,
    EvolutionSimulator
)
import uuid

# 1. Define genes (agent parameters to evolve)
genes = [
    Gene(
        gene_id="learning_rate",
        gene_type=GeneType.NUMERIC.value,
        allele=0.01,
        range_min=0.0001,
        range_max=0.1,
        mutation_probability=0.1
    ),
    Gene(
        gene_id="temperature",
        gene_type=GeneType.NUMERIC.value,
        allele=1.0,
        range_min=0.0,
        range_max=2.0,
        mutation_probability=0.05
    )
]

# 2. Create chromosome
chromosome = Chromosome(
    chromosome_id="chr_performance",
    chromosome_type=ChromosomeType.PERFORMANCE.value,
    genes=genes
)

# 3. Create genome
genome = AgentGenome(
    genome_id=str(uuid.uuid4()),
    generation=0,
    chromosomes=[chromosome]
)

# 4. Define fitness function
def fitness_function(genome):
    # Get learning rate
    _, lr_gene = genome.get_gene("learning_rate")
    # Optimal learning rate is 0.001
    lr_fitness = 1.0 - abs(lr_gene.allele - 0.001) / 0.01
    return max(0.0, lr_fitness)

# 5. Run evolution
simulator = EvolutionSimulator(
    population_size=20,
    mutation_rate=0.05,
    crossover_rate=0.7
)

simulator.initialize_population(genome)

stats = simulator.run(
    generations=10,
    fitness_function=fitness_function
)

# 6. Get evolved agent
best_agent = simulator.best_genome
print(f"Best fitness: {best_agent.fitness_score:.4f}")
```

### Collective Intelligence Protocol (CIP) - Harness Swarm Intelligence

```python
from src.superstandard.protocols.cip_v1 import (
    CollectiveDecision, VotingOption, Vote,
    WisdomOfCrowds, AgentEstimate,
    DecisionMethod, AggregationMethod
)

# 1. Collective Decision Making
options = [
    VotingOption("option_a", "Invest in AI"),
    VotingOption("option_b", "Market Expansion"),
]

votes = [
    Vote("strategic_lead", "option_a", weight=9.0, confidence=0.95),
    Vote("financial_lead", "option_a", weight=9.0, confidence=0.90),
    Vote("marketing_lead", "option_b", weight=4.0, confidence=0.85),
]

result = CollectiveDecision.make_decision(
    options,
    votes,
    method=DecisionMethod.QUADRATIC_VOTING
)

print(f"Decision: {result.winning_option}")
print(f"Consensus: {result.consensus_level:.1%}")

# 2. Wisdom of Crowds
estimates = [
    AgentEstimate("financial_agent", 15000000, confidence=0.9),
    AgentEstimate("sales_agent", 16500000, confidence=0.8),
    AgentEstimate("market_agent", 14200000, confidence=0.7),
]

crowd_result = WisdomOfCrowds.aggregate_estimates(
    estimates,
    method=AggregationMethod.CONFIDENCE_WEIGHTED
)

print(f"Collective estimate: ${crowd_result['aggregate']:,.0f}")
print(f"Confidence: {crowd_result['confidence']:.1%}")

# 3. Swarm Optimization
from src.superstandard.protocols.cip_v1 import SwarmOptimizer

def sphere_function(x):
    return sum(xi**2 for xi in x)

optimizer = SwarmOptimizer(dimensions=3, population_size=20)

result = optimizer.optimize(
    objective_function=sphere_function,
    bounds=[(-10, 10)] * 3,
    max_iterations=50,
    minimize=True
)

print(f"Optimal solution: {result['best_position']}")
```

## Complete Examples

### Run Full Demonstrations

```bash
# Agent evolution over 10 generations
python examples/adp_agent_evolution_demo.py

# Collective decision-making
python examples/cip_collective_decision_demo.py
```

## Testing

```bash
# Test ADP implementation
python src/superstandard/protocols/adp_v1.py

# Test CIP implementation
python src/superstandard/protocols/cip_v1.py

# Run unit tests (requires pytest)
pytest tests/unit/test_adp_v1.py -v
pytest tests/unit/test_cip_v1.py -v
```

## Documentation

- **Full Documentation:** `/home/user/multiAgentStandardsProtocol/docs/ADP_CIP_IMPLEMENTATION.md`
- **Implementation Summary:** `/home/user/multiAgentStandardsProtocol/IMPLEMENTATION_COMPLETE.md`
- **JSON Schemas:**
  - `specifications/schemas/adp-v1.0.schema.json`
  - `specifications/schemas/cip-v1.0.schema.json`

## Key Features

### ADP - Agent DNA Protocol
- ✅ Genetic representation (Gene, Chromosome, Genome)
- ✅ Mutation (point, insertion, deletion, duplication)
- ✅ Crossover (single-point, two-point, uniform)
- ✅ Selection (roulette wheel, tournament, elitism)
- ✅ Fitness evaluation
- ✅ Evolution simulation

### CIP - Collective Intelligence Protocol
- ✅ Knowledge pooling
- ✅ Collective decision-making
- ✅ Wisdom of crowds
- ✅ Consensus building
- ✅ Swarm optimization (PSO)
- ✅ Emergence metrics

---

**Ready to use!** Both protocols are production-ready and fully tested.
