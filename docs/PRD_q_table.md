# PRD — Q-Table Learning Agent (Optional Enhancement)

**Version:** 1.00
**Component:** `services/q_agent.py`

---

## 1. Description

An optional Q-learning layer that improves agent strategy over multiple episodes
by maintaining a Q-table mapping (state, action) pairs to expected rewards.
This is a tabular approach — no neural networks required.
The LLM agent remains the baseline; Q-learning is an enhancement.

## 2. Theoretical Background

### Formal Model
The pursuit game is modeled as a Dec-POMDP:
`⟨n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ⟩`

- **n = 2**: Cop and Thief agents
- **S**: all combinations of (cop_pos, thief_pos, barrier_positions)
- **Aᵢ**: {up, down, left, right} for Thief; + {place_barrier} for Cop
- **P**: transition function (deterministic given valid moves)
- **R**: reward function (see scoring table)
- **Ωᵢ**: partial observation per agent
- **γ = 0.9**: discount factor

### Bellman Equation
```
Q(s, a) ← Q(s, a) + α [r + γ · max_a' Q(s', a') − Q(s, a)]
```

## 3. Parameters (from config.json)

| Parameter | Type | Default | Description |
|---|---|---|---|
| q_learning.learning_rate (α) | float | 0.1 | How fast Q-values update |
| q_learning.discount_factor (γ) | float | 0.9 | Weight of future rewards |
| q_learning.epsilon | float | 0.2 | Exploration rate (ε-greedy) |
| q_learning.epsilon_decay | float | 0.995 | Epsilon decay per episode |
| q_learning.epsilon_min | float | 0.01 | Minimum exploration rate |

## 4. State Representation

State encoded as flat integer index:
- Grid position (row × cols + col) for each agent
- Barrier bitmask (one bit per cell)
- Combined into single hashable state key

## 5. Reward Function

| Event | Cop Reward | Thief Reward |
|---|---|---|
| Cop captures Thief | +20 | -20 |
| Thief escapes | -10 | +10 |
| Each step (fuel cost) | -1 | -1 |
| Moving toward opponent (Cop) | +0.5 | — |
| Moving away from Cop (Thief) | — | +0.5 |

## 6. Training Protocol

- Q-table initialized to zeros: shape (num_states, num_actions)
- Run N training episodes before evaluation
- ε-greedy policy: explore with probability ε, exploit otherwise
- Decay ε after each episode
- Save Q-table to `results/q_table_cop.npy` and `results/q_table_thief.npy`

## 7. Success Criteria

- [ ] Q-table initializes correctly for given grid size
- [ ] Bellman update applied correctly after each step
- [ ] ε-greedy policy switches between explore/exploit correctly
- [ ] Q-table persisted to disk and loadable
- [ ] Win rate improves over training episodes (shown in graph)
- [ ] Sensitivity analysis: learning_rate and discount_factor variations documented
