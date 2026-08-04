/dl-model-advisor:advise 4,000 support tickets (about 120 words each) labeled urgent or not-urgent. Give me the plan and the starter training script.

End state: a model plan in MODEL_PLAN.md plus runnable starter code in starter_model.py in this directory. Proof: python3 -m py_compile starter_model.py exits 0 and the plan states architecture, loss, activation, and protocol.

Do not access the network. Stop after at most 40 turns.
