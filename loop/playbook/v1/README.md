# Playbook v1 (mutable; versioned)

Role separation for every major claim (user steering A):
- Research Director (the PI loop): picks branches, writes preregistrations, never grades its own claims.
- Investigators: fresh agents that run or recompute a defined analysis from raw files, with no access to the PI's reasoning.
- Critic: a fresh agent that tries to break a claim (alternative explanations, confounds, prior art).
- Evidence Verifier: a fresh agent that matches each claim to an artifact and labels it VERIFIED, PARTIALLY VERIFIED, UNVERIFIED or CONTRADICTED in results/claim_evidence.md.

Reviewer lenses follow loop/RUBRIC.md (locked). Prompts: reviewer_*.md in this folder.
Failure taxonomy for subject calls: failure_taxonomy.md.
