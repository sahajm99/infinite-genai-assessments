# LLM Agents in Production (SYNTHETIC SEED CORPUS)

## What agents are
An LLM agent couples a language model with tools, memory, and a control loop so it can plan
and take multi-step actions toward a goal, rather than producing a single response.

## Reliability challenges
Agents accumulate error across steps: a small mistake early can compound over a long
trajectory. Common failure modes include hallucinated tool arguments, infinite loops, and
losing track of the goal. Guardrails such as step limits, validation of tool inputs, and
structured outputs reduce these failures.

## Orchestration frameworks
Frameworks like LangGraph model an agent as a state machine or graph, making control flow
explicit and debuggable. This is more predictable than free-form agent loops because each
node's responsibility and transitions are defined up front.

## Evaluation
Evaluating agents requires more than checking a final answer. Teams measure task success
rate, number of steps, tool-call accuracy, and cost per task. Trajectory-level evaluation
and human review remain important because automated metrics miss subtle reasoning errors.

## Cost and latency
Multi-step agents can be expensive and slow because each step is a model call. Techniques
to control this include caching, using smaller models for routing, running independent
sub-tasks concurrently, and limiting the maximum number of steps.

## Security and risk
Giving an agent tools (code execution, web access, database queries) expands the attack
surface. Prompt injection can hijack an agent's behavior. Mitigations include least-
privilege tool scoping, human approval for high-impact actions, and sandboxing.
