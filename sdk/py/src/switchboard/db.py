from botocore.utils import ClientError
from abc import ABC, abstractmethod
from boto3.dynamodb.conditions import Key

from .schemas import NewState, State
from .enums import SwitchboardComponent, TableName, Cloud
from .cloud import (
        AWS_db_connect,
        GCP_db_connect, 
        AZURE_db_connect, 
        UnsupportedCloud
        )




# Database Interface
class DBInterface(ABC):
    '''
    Abstract base class for implementing a switchboard database interface.

    Parameters:
        conn: A specific database connection object. 
            This will be available to interact with via `self.conn` when implementing the required methods of this interface.

    Subclasses must implement the following methods:
        - read(name, id): Retrieves the state associated with the given `name` and `run id`.
        - write(state): Stores or updates the `State` associated with the workflow `name` and `run_id`.
        - increment_id(name): Atomically increment a counter to generate the `run_id` for a given workflow identified by `name`.

    Example:
        ```python 
        import redis
        from switchbord import DBInterface, DB, Cloud

        class CustomInterface(DBInterface):
            def read(self, name, id):
                # Custom read logic 

            def write(self, state):
                # Custom write logic

            def increment_id(self, name):
                # Custom increment logic

        conn = CustomInterface(redis.Redis(host='myendpoint', port=6379))
        db = DB(Cloud.CUSTOM, conn)
        ```
    '''
    def __init__(self, conn) -> None:
        super().__init__()
        self.conn = conn

    @abstractmethod
    def read(self, name: str, id: int) -> State | None:
        pass

    @abstractmethod
    def write(self, state: State):
        pass

    @abstractmethod
    def increment_id(self, name: str) -> int:
        pass
    
    @abstractmethod
    def get_endpoint(self, name: str, component: SwitchboardComponent) -> str:
        pass
    
    @abstractmethod
    def get_table(self, table: TableName):
        pass



class AWS_DataInterface(DBInterface):
    '''
    Default database interface for AWS. Uses dynamodb.

    Table Schemas:
        ```js
        SwitchboardState: {
            "name":        "string",   // Partition key — represents the workflow name
            "run_id":      "number",   // Sort key — monotonically increasing run ID within each name
            "steps":       "list",     // List of steps or tasks executed during the run and the status of each
            "cache":       "map"       // Dictionary-like structure storing any cached data or intermediate results
        }

        SwitchboardResources: {
            "component":        "string",   // The type of component (see enums.SwitchboardComponent)
            "url":              "string",   // The endpoint url
            "cloud":            "string",   // The cloud provider (see enums.Cloud)
            "resource":         "string",   // The specific resource being used for the component (see enums.CloudResource)
            "resource_type":    "string"    // The type of resource the component is (see enums.CloudResourceType)
        }
        ```

    '''
    def read(self,name,id):
        tbl = self.get_table()
        state = None
        try:
            response = tbl.get_item(Key={"name": name, "run_id": id})
        except ClientError as err:
            raise Exception(
                "%s - Couldn't get state for run_id %s from table %s. %s: %s",
                name,
                id,
                tbl.table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
        else:
            state = NewState(response["Item"])
        finally:
            return state

    def write(self,state):
        tbl = self.get_table()
        try:
            response = tbl.update_item(
                Key={"name": state.name, "run_id": state.run_id},
                UpdateExpression="set steps=:steps, cache=:cache",
                ExpressionAttributeValues={":steps": state.steps, ":cache": state.cache},
            )
        except ClientError as err:
           raise Exception(
                "%s - Couldn't update state for run_id %s to table %s. %s: %s",
                state.name,
                state.run_id,
                tbl.table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
        else:
            assert response['ResponseMetadata']['HTTPStatusCode'] == 200
            

    def increment_id(self,name):
        tbl = self.get_table()
        response = tbl.query(
            KeyConditionExpression=Key('name').eq(name),
            ScanIndexForward=False,  
            Limit=1 
        )

        items = response.get('Items', [])
        latest_run_id = items[0]['run_id'] if items else 0
        return latest_run_id + 1


    def get_endpoint(self, name, component) -> str:
        tbl = self.get_table(TableName.SwitchboardResources)
        try:
            ep = tbl.get_item(Key={"component": component, "name": name})
        except ClientError as err:
            raise Exception(
                "%s - Couldn't get endpoint for %s from table %s. %s: %s",
                name,
                component,
                tbl.table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
        return ep


    def get_table(self,table=TableName.SwitchboardState):
        tbl = self.conn.Table(table)
        return tbl



# class GCP_DataInterface(DBInterface):
#     def read(self,name,id):
#         pass
#
#     def write(self,name,state):
#         pass
#
#     def increment_id(self,name,id):
#         pass
#
#
# class AZURE_DataInterface(DBInterface):
#     def read(self,name,id):
#         pass
#
#     def write(self,name,state):
#         pass
#
#     def increment_id(self,name,id):
#         pass


# SDK database interface initializer
class DB():
    '''
    Class for establishing a connection for switchboard to interface with. switchboard comes with a default interface for each cloud provider.
    Use the custom_interface arg to pass in your own custom interface.
    '''
    def __init__(self, cloud: Cloud, custom_interface: DBInterface | None = None) -> None:
        def _connect(cloud: Cloud) -> DBInterface:
            match cloud:
                case Cloud.AWS:
                    conn = AWS_db_connect()
                    return AWS_DataInterface(conn)
                # case Cloud.GCP:
                #     conn = GCP_db_connect()
                #     return GCP_DataInterface(conn)
                # case Cloud.AZURE:
                #     conn = AZURE_db_connect()
                #     return AZURE_DataInterface(conn)
                case Cloud.CUSTOM:
                    assert custom_interface
                    return custom_interface
                case _:
                    raise UnsupportedCloud(f"Attempted to connect to an unsupported cloud: {cloud}")

        self.cloud = cloud
        self.interface = _connect(cloud)





