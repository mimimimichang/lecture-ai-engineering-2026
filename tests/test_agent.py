"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

import sys

from pydantic_ai import DeferredToolRequests, DeferredToolResults
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import agent as agent_module
from app import tools
from app.agent import agent

BASE_TOOLS = {"search_glossary", "get_lecture_summary"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
    model = TestModel(call_tools=sorted(BASE_TOOLS))
    with agent.override(model=model):
        result = agent.run_sync("LoRAとは？")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # 演習でツールを足しても壊れないよう「含む」で判定

    called = {p.tool_name for p in _parts(result, ToolCallPart)}
    assert BASE_TOOLS <= called
    assert len(_parts(result, ToolReturnPart)) == len(_parts(result, ToolCallPart))
    assert result.output


def test_save_learning_log_waits_for_approval(tmp_path, monkeypatch):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", log_dir)
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        pending = agent.run_sync("今日の学習を記録して")

    assert isinstance(pending.output, DeferredToolRequests)
    assert len(pending.output.approvals) == 1
    request = pending.output.approvals[0]
    assert request.tool_name == "save_learning_log"
    assert not list(log_dir.glob("*.md"))

    with agent.override(model=TestModel(call_tools=[])):
        result = agent.run_sync(
            None,
            message_history=pending.all_messages(),
            deferred_tool_results=DeferredToolResults(
                approvals={request.tool_call_id: True}
            ),
        )

    saved_files = list(log_dir.glob("*.md"))
    assert len(saved_files) == 1
    assert saved_files[0].read_text(encoding="utf-8").strip() == request.args["entry"]
    assert any(p.tool_name == "save_learning_log" for p in _parts(result, ToolReturnPart))


def test_save_learning_log_can_be_declined(tmp_path, monkeypatch):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", log_dir)
    with agent.override(model=TestModel(call_tools=["save_learning_log"])):
        pending = agent.run_sync("今日の学習を記録して")
    request = pending.output.approvals[0]

    with agent.override(model=TestModel(call_tools=[])):
        agent.run_sync(
            None,
            message_history=pending.all_messages(),
            deferred_tool_results=DeferredToolResults(
                approvals={request.tool_call_id: False}
            ),
        )

    assert not list(log_dir.glob("*.md"))


def test_cli_asks_before_saving_and_resumes(tmp_path, monkeypatch, capsys):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", log_dir)
    monkeypatch.setattr(sys, "argv", ["app.agent", "今日の学習を記録して"])
    prompts = []
    monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or "y")
    models = iter(
        [TestModel(call_tools=["save_learning_log"]), TestModel(call_tools=[])]
    )
    monkeypatch.setattr(agent_module, "build_model", lambda: next(models))

    agent_module.main()

    assert len(list(log_dir.glob("*.md"))) == 1
    assert prompts and "次の内容を保存しますか？" in prompts[0]
    assert "学習ログを保存しました" in capsys.readouterr().out


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("RAGとは？")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"
