import pytest
from switchboard.workflow import Workflow, Context

class DBMock: 
    def read(self, *args):
        return None

    def write(self, *args):
        return None

db = DBMock()

def test_something():
    context = '{}'
    workflow = Workflow(db, context)
    expected = Context([0,0], False)
    assert workflow._get_context(context) == expected


