"""Simulated learner pilot: a quiz from the objectives and run data, taken before and after seeing the deck.
The quiz writer never sees the deck, so a post-test gain means the deck conveyed what the week should teach."""
from typing import Any, Dict, List, Optional

from digitalagedu.core.eval.llm import clip, structured, user_content
from digitalagedu.core.eval.load import WeekBundle
from digitalagedu.core.eval.schemas import Quiz, QuizAnswers


def write_quiz(client, model: str, bundle: WeekBundle, run_facts: str, student_level: str) -> Quiz:
    objectives = "\n".join(f"{i}. {o}" for i, o in enumerate(bundle.objectives)) or "0. (no objectives recorded)"
    return structured(
        client, model, Quiz,
        "You write multiple-choice quizzes that measure what a lesson taught. Each question has 4 options and one "
        "correct answer, with plausible distractors.",
        f"STUDENT LEVEL: {student_level}\nLESSON: Week {bundle.week}, {bundle.module_id}\n\n"
        f"LEARNING OBJECTIVES (0-based):\n{objectives}\n\nRUN DATA:\n{clip(run_facts, 4000)}\n\n"
        "Write 10 questions: 7 of kind 'run_data' whose answers are specific facts or findings in the RUN DATA above "
        "(a student could only know them from this lesson), and 3 of kind 'concept' testing understanding of the "
        "objectives. Tag each with the objective it assesses. Vary the position of the correct option.",
    )


def take_quiz(client, model: str, quiz: Quiz, student_level: str, slide_pngs: Optional[List[str]] = None,
              slide_texts: Optional[List[str]] = None) -> List[int]:
    """Answers from the learner persona; with no slides given, this is the pre-test."""
    questions = "\n\n".join(f"Q{i}. {q.question}\n" + "\n".join(f"  {j}) {o}" for j, o in enumerate(q.options))
                            for i, q in enumerate(quiz.questions))
    if slide_pngs:
        material = "You have just studied this lesson's slides (shown after the questions)."
    elif slide_texts:
        material = "You have just studied this lesson's slides:\n" + "\n\n".join(
            f"[Slide {i + 1}]\n{t}" for i, t in enumerate(slide_texts))
    else:
        material = "You have not seen the lesson yet."
    reply = structured(
        client, model, QuizAnswers,
        f"You are a {student_level} student taking a quiz. Answer only from what a {student_level} student would "
        "know plus the lesson material you are given. Do not use outside expert knowledge; if you don't know, guess.",
        user_content(f"{material}\n\nAnswer each question with the option number (0-3).\n\n{questions}", slide_pngs),
        max_tokens=4096,
    )
    return reply.answers


def score(quiz: Quiz, pre: List[int], post: List[int]) -> Dict[str, Any]:
    """Per-question correctness and accuracy/gain overall, by kind and by objective. Missing answers count wrong."""
    rows = []
    for i, q in enumerate(quiz.questions):
        rows.append({"kind": q.kind, "objective_index": q.objective_index,
                     "pre": int(i < len(pre) and pre[i] == q.answer_index),
                     "post": int(i < len(post) and post[i] == q.answer_index)})

    def summary(sel: List[Dict[str, Any]]) -> Dict[str, Any]:
        n = len(sel)
        pre_acc = sum(r["pre"] for r in sel) / n if n else None
        post_acc = sum(r["post"] for r in sel) / n if n else None
        return {"n": n, "pre": pre_acc, "post": post_acc, "gain": None if n == 0 else post_acc - pre_acc}

    return {
        "overall": summary(rows),
        "by_kind": {k: summary([r for r in rows if r["kind"] == k]) for k in ("run_data", "concept")},
        "by_objective": {str(o): summary([r for r in rows if r["objective_index"] == o])
                         for o in sorted({r["objective_index"] for r in rows})},
        "per_question": rows,
    }
