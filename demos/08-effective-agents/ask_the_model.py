# קובץ 6 – הבחירה
# אותה הודעה, ארבע דרכים. רק מי שולט בזרימה משתנה.

from agent import run_agent
from llm_client import notice
from prompt import MODE_AGENT, MODE_EVAL, MODE_PARALLEL, MODE_ROUTING
from recorder import Trace
from workflows import run_eval_loop, run_parallel, run_routing

RUNNERS = {
    MODE_AGENT: (run_agent, "המודל"),
    MODE_ROUTING: (run_routing, "הקוד"),
    MODE_PARALLEL: (run_parallel, "הקוד"),
    MODE_EVAL: (run_eval_loop, "הקוד"),
}


def ask(text: str, mode: str) -> dict:
    run, controller = RUNNERS[mode]
    trace = Trace()
    trace.say(f"המשתמשת שלחה: {text}")
    answer = run(text, trace)
    return {
        "answer": answer,
        "control": f"**מי שולט בזרימה:** {controller} · **קריאות למודל:** {trace.calls}",
        "prompt": trace.prompt_text() or "(לא נשלח פרומפט למודל)",
        "what_happened": trace.numbered_steps(),
        "notice": notice(),
    }
