import pytest
from bluemarz.core.exceptions import InvalidDefinition
from bluemarz.core.class_registry import assignment_executor, get_executor
from test.unit.mocks.core import MockAgent, MockExecutor, MockSession

def test_get_executor():
    assert get_executor(MockAgent(), MockSession()) == MockExecutor

def test_assignment_executor_register_fails_invalid_class():
    with pytest.raises(TypeError):
        @assignment_executor
        class NotExecutor():
            pass

def test_assignment_executor_register_fails_duplicate_assignment():
    with pytest.raises(InvalidDefinition) as einfo:
        @assignment_executor
        class DuplicateExecutor(MockExecutor):
            pass
        
    for part in ["MockAgent","MockSession"]:
        assert part in str(einfo.value)

def test_get_executor_throws_for_unregistered():
    class UnregisteredAgent(MockAgent):
        pass

    class UnregisteredSession(MockSession):
        pass

    with pytest.raises(InvalidDefinition, match="UnregisteredAgent"):
        get_executor(UnregisteredAgent(), MockSession())
    
    with pytest.raises(InvalidDefinition, match="UnregisteredSession"):
        get_executor(MockAgent(), UnregisteredSession())

    with pytest.raises(InvalidDefinition) as einfo:
        get_executor(UnregisteredAgent(), UnregisteredSession())
    for part in ["UnregisteredAgent","UnregisteredSession"]:
        assert part in str(einfo.value)