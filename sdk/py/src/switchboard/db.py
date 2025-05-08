from typing import Callable
from .cloud import (
        AWS_DataInterface, 
        AWS_db_connect,
        GCP_DataInterface, 
        GCP_db_connect, 
        AZURE_DataInterface, 
        AZURE_db_connect, 
        DBInterface, 
        UnsupportedCloud
        )
from .enums import Cloud






class DB():
    def __init__(self, cloud: Cloud, custom_con: Callable | None = None, custom_interface: DBInterface | None = None) -> None:
        def _connect(cloud: Cloud, custom: Callable | None = None):
            match cloud:
                case Cloud.AWS:
                    AWS_db_connect()
                case Cloud.GCP:
                    GCP_db_connect()
                case Cloud.AZURE:
                    AZURE_db_connect()
                case Cloud.CUSTOM:
                    assert custom
                    custom()
                case _:
                    raise UnsupportedCloud(f"Attempted to connect to an unsupported cloud: {cloud}")
            return
        self._cloud = cloud
        self._conn = _connect(cloud, custom_con)
        self._actions = {
                Cloud.AWS: AWS_DataInterface(),
                Cloud.GCP: GCP_DataInterface(),
                Cloud.AZURE: AZURE_DataInterface(),
                Cloud.CUSTOM: custom_interface # user must instantiate their custom interface instance
                }


    def read(self, id):
        return self._actions[self._cloud].read(id)

    def write(self, id, state):
        return self._actions[self._cloud].write(id, state)

    def increment_id(self, id):
        return self._actions[self._cloud].increment_id(id)




