"""Apply the GPT->SAGE boundary at the legacy ChatGPT integration seam."""

from pathlib import Path


TARGET = Path("sage/integration.py")
START = "        # 2. Failure Ordering: API Key Check -> API Call -> Successful Output -> Ingestion\n"
END = "        # Protocol Governance validation on response_text\n"

REPLACEMENT = '''        # 2. The model call MUST traverse the SAGE C2 boundary before output is returned.
        from sage.c2.chatgpt_sage_boundary import execute_sage_bound_chatgpt_from_legacy_runtime

        try:
            bound = execute_sage_bound_chatgpt_from_legacy_runtime(
                runtime=self.runtime,
                session_id=session_id,
                task=request.prompt,
                c2_context=c2_context,
                response_override=request.response_override,
            )
            response_text = bound.raw_output
            reasoning = (
                f"ChatGPT traversed SAGE C2 runtime boundary for prompt: "
                f"'{request.prompt[:50]}...'"
            )
            self.reasoning_history.append(reasoning)
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            raise RuntimeError(f"SAGE C2 boundary execution failed: {e}") from e

'''


def main() -> None:
    source = TARGET.read_text()
    if "execute_sage_bound_chatgpt_from_legacy_runtime" in source:
        print("ChatGPT integration boundary already wired")
        return
    start = source.find(START)
    end = source.find(END, start)
    if start < 0 or end < 0:
        raise SystemExit("FAIL CLOSED: ChatGPT integration seam not found")
    TARGET.write_text(source[:start] + REPLACEMENT + source[end:])
    print("Patched ChatGPT integration through SAGE C2 boundary")


if __name__ == "__main__":
    main()
