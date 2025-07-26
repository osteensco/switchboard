from switchboard.db import DBInterface
from switchboard.schemas import State



class DBMockInterface(DBInterface):
    def __init__(self, state: State | None) -> None:
        self.all_states, self.id_max = self._prepopulate(state)

    def _prepopulate(self, state: State | None) -> tuple[dict, int]:
        if state:
            return {state.run_id: state}, state.run_id
        return {}, 0

    def read(self, name, id):
        try:
            state = self.all_states[id]
            return state
        except KeyError:
            print(f"!!!!!! key `{id}` not found! all_states: {self.all_states}")
            return None

    def write(self, state):
        self.all_states[state.run_id] = state

    def get_endpoint(self, name, component):
        return "mocked/endpoint"

    def increment_id(self, name):
        self.id_max += 1
        return self.id_max

    def get_table(self, table):
        pass
    

