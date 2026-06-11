from app.main import EXIT_KEYWORDS, _print_banner, _print_decision
from app.schemas import AgentName, RoutingDecision


def test_exit_keywords_contains_expected_values() -> None:
    assert {"exit", "quit", "q"} == EXIT_KEYWORDS


def test_print_banner(capsys) -> None:
    _print_banner()

    captured = capsys.readouterr()
    assert captured.out == "JARVIS2026 CLI\nType a request, or 'exit' to quit.\n"


def test_print_decision(capsys) -> None:
    decision = RoutingDecision(
        request_id="00000000-0000-0000-0000-000000000000",
        primary_agent=AgentName.DEV,
        secondary_agents=[],
        confidence=0.85,
        reasoning="Test routing decision",
        matched_keywords=["test", "debug"],
    )

    _print_decision(decision)
    captured = capsys.readouterr()

    assert "Primary agent: dev\n" in captured.out
    assert "Confidence: 0.85\n" in captured.out
    assert "Matched keywords: test, debug\n" in captured.out
    assert "Reasoning: Test routing decision\n" in captured.out
