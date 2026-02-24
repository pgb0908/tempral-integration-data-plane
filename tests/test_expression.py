from __future__ import annotations

import pytest

from flow_engine.expression.evaluator import ExpressionEvaluator
from flow_engine.expression.sandbox import AttrDict


def test_attr_dict_access():
    d = AttrDict({"name": "Alice", "nested": {"age": 30}})
    assert d.name == "Alice"
    assert d.nested.age == 30


def test_attr_dict_missing():
    d = AttrDict({})
    with pytest.raises(AttributeError):
        _ = d.missing


def test_plain_string_passthrough():
    ev = ExpressionEvaluator()
    assert ev.evaluate("hello") == "hello"


def test_integer_passthrough():
    ev = ExpressionEvaluator()
    assert ev.evaluate(42) == 42


def test_json_field_expression():
    ev = ExpressionEvaluator(current_item={"name": "World"})
    result = ev.evaluate('={{ "Hello " + $json.name }}')
    assert result == "Hello World"


def test_json_numeric_expression():
    ev = ExpressionEvaluator(current_item={"value": 10})
    result = ev.evaluate("={{ $json.value * 2 }}")
    assert result == 20


def test_node_accessor():
    node_results = {
        "PrevNode": {
            "node_name": "PrevNode",
            "node_id": "1",
            "status": "success",
            "output_data": [[{"score": 99}]],
        }
    }
    ev = ExpressionEvaluator(current_item={}, node_results=node_results)
    result = ev.evaluate("={{ $node['PrevNode'].json.score }}")
    assert result == 99


def test_mixed_expression():
    ev = ExpressionEvaluator(current_item={"first": "John", "last": "Doe"})
    result = ev.evaluate('={{ $json.first }} ={{ $json.last }}')
    assert result == "John Doe"


def test_evaluate_parameters():
    ev = ExpressionEvaluator(current_item={"x": 5})
    params = {
        "label": '={{ "value=" + str($json.x) }}',
        "nested": {"doubled": "={{ $json.x * 2 }}"},
        "plain": "no expression",
    }
    result = ev.evaluate_parameters(params)
    assert result["label"] == "value=5"
    assert result["nested"]["doubled"] == 10
    assert result["plain"] == "no expression"


def test_invalid_expression_raises():
    ev = ExpressionEvaluator(current_item={})
    with pytest.raises(ValueError):
        ev.evaluate("={{ undefined_var }}")
