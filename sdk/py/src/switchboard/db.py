from botocore.utils import ClientError
from .schemas import State
from .enums import TableName, Cloud
from .cloud import (
        AWS_db_connect,
        GCP_db_connect, 
        AZURE_db_connect, 
        UnsupportedCloud
        )
from abc import ABC, abstractmethod
import boto3





# Database Interface
class DBInterface(ABC):
    '''
    Abstract base class for implementing a switchboard database interface.

    Parameters:
        conn: A specific database connection object. 
            This will be available to interact with via `self.conn` when implementing the required methods of this interface.

    Subclasses must implement the following methods:
        - read(id): Retrieves the state associated with the given `run id`.
        - write(id, state): Stores or updates the `State` associated with the given `run id`.
        - increment_id(id): Atomically increment a counter to generate the `step id` in a given workflow.

    Example:
        ```python 
        class CustomInterface(DBInterface):
            def read(self, id):
                # Custom read logic 

            def write(self, id, state):
                # Custom write logic

            def increment_id(self, id):
                # Custom increment logic

        db = CustomInterface(redis.Redis(host='myendpoint', port=6379))
        ```
    '''
    def __init__(self, conn) -> None:
        super().__init__()
        self.conn = conn

    @abstractmethod
    def read(self, name: str, id: int):
        pass

    @abstractmethod
    def write(self, name: str, state: State):
        pass

    @abstractmethod
    def increment_id(self, name: str, id: int):
        pass



class AWS_DataInterface(DBInterface):
    '''
    Default database interface for AWS. Uses dynamodb.
    '''
    def read(self,name,id):
        tbl = self.get_table()
        try:
            response = tbl.get_item(Key={"name": name, "run_id": id})
        except ClientError as err:
            raise Exception(
                "Couldn't get state for run_id %s from table %s. %s: %s",
                id,
                tbl.table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
        else:
            return response["Item"]

    def write(self,name,state):
        tbl = self.get_table()
        try:
            response = tbl.update_item(
                Key={"name": name, "run_id": state.run_id},
                UpdateExpression="set steps=:steps, cache=:cache",
                ExpressionAttributeValues={":steps": state.steps, ":cache": state.cache},
            )
        except ClientError as err:
           raise Exception(
                "Couldn't update state for run_id %s to table %s. %s: %s",
                id,
                tbl.table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
        else:
            assert response['ResponseMetadata']['HTTPStatusCode'] == 200
            

    def increment_id(self,name,id):
        pass

    def get_table(self,table=TableName.Dynamodb):
        tbl = self.conn.Table(table)
        return tbl



class GCP_DataInterface(DBInterface):
    def read(self,name,id):
        pass

    def write(self,name,state):
        pass

    def increment_id(self,name,id):
        pass


class AZURE_DataInterface(DBInterface):
    def read(self,name,id):
        pass

    def write(self,name,state):
        pass

    def increment_id(self,name,id):
        pass


# SDK database interface
class DB():
    def __init__(self, cloud: Cloud, custom_interface: DBInterface | None = None) -> None:
        def _connect(cloud: Cloud) -> DBInterface:
            match cloud:
                case Cloud.AWS:
                    conn = AWS_db_connect()
                    return AWS_DataInterface(conn)
                case Cloud.GCP:
                    conn = GCP_db_connect()
                    return GCP_DataInterface(conn)
                case Cloud.AZURE:
                    conn = AZURE_db_connect()
                    return AZURE_DataInterface(conn)
                case Cloud.CUSTOM:
                    assert custom_interface
                    return custom_interface
                case _:
                    raise UnsupportedCloud(f"Attempted to connect to an unsupported cloud: {cloud}")

        self.cloud = cloud
        self.interface = _connect(cloud)





