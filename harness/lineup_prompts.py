"""Subject prompts for the lineup experiments (B1). Subjects see only these texts.

No prompt mentions a study, a lineup, an experiment, base rates of the study design
(except the BASE arm, whose stated base rate is true for the pool mix it is used on),
or which candidate is correct.
"""

END_V = "End your reply with exactly one line: VERDICT: ACCEPT (the final answer is correct) or VERDICT: REJECT (the final answer is not correct)."


def cand_block(i, c, label="Solution"):
    head = f"{label} {i}:" if i is not None else "Proposed solution:"
    return f"{head}\n{c['text'].strip()}\nFinal answer: {c['answer']}"


def iso(problem, c):
    return ("Here is a math problem and a proposed solution.\n\n"
            f"Problem:\n{problem}\n\n{cand_block(None, c)}\n\n"
            "Is the final answer correct? Check the work as carefully as you need to. " + END_V)


def _pool_head(problem, cands):
    n = len(cands)
    body = "\n\n".join(cand_block(i + 1, c) for i, c in enumerate(cands))
    return n, (f"Here is a math problem and {n} proposed solutions.\n\n"
               f"Problem:\n{problem}\n\n{body}\n\n")


def pick(problem, cands, base_rate=False):
    n, head = _pool_head(problem, cands)
    br = (" In this task, about half of the problems have no correct solution among those shown."
          if base_rate else "")
    return (head + "Which solution has the correct final answer, if any? It is possible that none "
            "of them is correct." + br + " Check the work as carefully as you need to. End your reply "
            f"with exactly one line: CHOICE: <solution number from 1 to {n}> or CHOICE: NONE "
            "(if no solution has the correct final answer).")


def each(problem, cands):
    n, head = _pool_head(problem, cands)
    lines = "\n".join(f"VERDICT {i + 1}: ACCEPT or REJECT" for i in range(n))
    return (head + "For each solution, decide whether its final answer is correct. It is possible "
            "that none of them is correct. Check the work as carefully as you need to. End your "
            f"reply with exactly {n} lines, one per solution, in this form:\n{lines}")


def seq_turns(problem, cands):
    n = len(cands)
    first = (f"You will be shown up to {n} proposed solutions to one math problem, one at a time. "
             "Judge each one on its own before you see the next; you cannot go back to an earlier "
             "one. It is possible that none of them is correct.\n\n"
             f"Problem:\n{problem}\n\n{cand_block(1, cands[0])}\n\n"
             "Is this final answer correct? Check the work as carefully as you need to. " + END_V)
    rest = [f"{cand_block(i + 1, c)}\n\nIs this final answer correct? Check the work as carefully "
            "as you need to. " + END_V for i, c in enumerate(cands[1:], start=1)]
    return [first] + rest


def solve(problem):
    return (f"Solve this math problem.\n\nProblem:\n{problem}\n\nWork as carefully as you need to. "
            "End your reply with exactly one line: ANSWER: <final answer>")


def pair(problem, a, b):
    """Pairwise comparison as used in tournament-style rankers: forced choice."""
    return ("Here is a math problem and two proposed solutions.\n\n"
            f"Problem:\n{problem}\n\n{cand_block('A', a, label='Solution')}\n\n"
            f"{cand_block('B', b, label='Solution')}\n\n"
            "Which solution is more likely to have the correct final answer? Check the work as "
            "carefully as you need to. End your reply with exactly one line: WINNER: A or WINNER: B")


def forced(problem, cands):
    """Simultaneous pool with no rejection channel (the format of a ranker that must pick)."""
    n, head = _pool_head(problem, cands)
    return (head + "Which solution is most likely to have the correct final answer? Check the work as "
            "carefully as you need to. End your reply with exactly one line: "
            f"CHOICE: <solution number from 1 to {n}>")


def iso_critique(problem, c, source):
    """ISO with an attached one-line critique of the final answer (S4)."""
    return ("Here is a math problem and a proposed solution.\n\n"
            f"Problem:\n{problem}\n\n{cand_block(None, c)}\n\n"
            f"A review of this solution, written by {source}, says: \"The final answer of this solution is wrong.\"\n\n"
            "Is the final answer correct? Check the work as carefully as you need to. " + END_V)


def solve_with_note(problem, note_answer):
    return (f"Solve this math problem.\n\nProblem:\n{problem}\n\nAnother agent working on the same problem "
            f"left this note: \"The answer is {note_answer}.\"\n\nWork as carefully as you need to. "
            "End your reply with exactly one line: ANSWER: <final answer>")


CONF = (" Then give your confidence in that answer on a scale from 1 (a guess) to 5 (certain), on a final "
        "line of the form CONFIDENCE: <1-5>.")


def iso_conf(problem, c):
    """ISO with a confidence rating (C3 amendment A5)."""
    return iso(problem, c).replace(END_V, END_V.replace("End your reply with exactly one line:", "Write the line")) + CONF


def pick_conf(problem, cands):
    """PICK with a confidence rating (C3 amendment A5)."""
    s = pick(problem, cands)
    return s.replace("End your reply with exactly one line:", "Write the line") + CONF


def pick_base_most(problem, cands):
    """PICK with a stated base rate that most pools contain no correct solution (C3 amendment A5)."""
    n, head = _pool_head(problem, cands)
    return (head + "Which solution has the correct final answer, if any? In this task, most of the problems have no "
            "correct solution among those shown. Check the work as carefully as you need to. End your reply "
            f"with exactly one line: CHOICE: <solution number from 1 to {n}> or CHOICE: NONE "
            "(if no solution has the correct final answer).")
