#!/usr/bin/env python3
"""Quick smoke test for the config + LLM factory layers."""
import sys
sys.path.insert(0, ".")

def test_config():
    from src.config.settings import get_settings
    s = get_settings()
    assert s.llm.get("task_providers"), "task_providers missing"
    assert s.get_task_provider("chat") == "llamacpp", f"Expected llamacpp, got {s.get_task_provider('chat')}"
    assert s.auth_mode == "none"
    print("[PASS] config.yaml loads and resolves correctly")
    print("  task_providers:", s.llm.get("task_providers"))
    print("  auth_mode:", s.auth_mode)
    print("  active_decorators:", s.get_active_decorators())
    print("  enabled_integrations:", s.get_enabled_integrations())

def test_provider_config():
    from src.config.settings import get_settings
    s = get_settings()
    cfg = s.get_provider_config("llamacpp")
    assert cfg.get("model_path"), "model_path not set"
    print("[PASS] provider config resolved:", cfg)

def test_decorator_registry():
    from src.graph.decorators.registry import DecoratorRegistry
    registered = DecoratorRegistry.list_registered()
    assert "exam_mode" in registered, f"exam_mode not registered: {registered}"
    assert "socratic_mode" in registered
    assert "strict_pacing" in registered
    print("[PASS] DecoratorRegistry:", registered)

def test_llm_factory_import():
    from src.llm.factory import PROVIDER_REGISTRY
    assert "llamacpp" in PROVIDER_REGISTRY
    assert "openai" in PROVIDER_REGISTRY
    assert "anthropic" in PROVIDER_REGISTRY
    print("[PASS] PROVIDER_REGISTRY:", list(PROVIDER_REGISTRY.keys()))

def test_graph_state():
    from src.graph.state import TutorState
    state: TutorState = {
        "user_id": "test", "session_id": "s1", "messages": [],
        "topic": None, "subtopic": None, "plan": None, "intent": None,
        "evaluation_result": None, "mastery_level": None,
        "active_decorators": [], "knowledge_items": None,
        "last_feedback": None, "iteration_count": 0, "error": None,
    }
    assert state["user_id"] == "test"
    print("[PASS] TutorState instantiates OK")

if __name__ == "__main__":
    tests = [test_config, test_provider_config, test_decorator_registry,
             test_llm_factory_import, test_graph_state]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1
    print(f"\n{'All tests passed!' if failed == 0 else f'{failed} test(s) failed.'}")
    sys.exit(failed)
