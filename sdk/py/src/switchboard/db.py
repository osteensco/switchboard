from botocore.utils import ClientError
from abc import ABC, abstractmethod
from boto3.dynamodb.conditions import Key

from .schemas import NewState, State
from .enums import SwitchboardComponent, TableName, Cloud
from .cloud import (
        AWS_db_connect,
        # GCP_db_connect, 
        # AZURE_db_connect, 
        UnsupportedCloud
        )



#TODO
# - If a user creates a custom DBInterface, this would need to be included in the workflow and executor functions.
#   This means that a custom DBInterface should probably be added in a separate .py file and imported in both workflow and executor function files.
#   Need to account for this in documentation and the cli tool's deployer.

# Database Interface
class DBInterface(ABC):
    '''
    Abstract base class for implementing a switchboard database interface.
    Note that the out-of-the-box database interfaces switchboard provides are all built off of this interface. 
    This class is available in the API to allow users the capability to create custom database interfaces for data persistence solutions of their choosing.

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
            "cache":       "map",       // Dictionary-like structure storing any cached data or intermediate results
            "status":       "string"    // String representation of Status enum
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
        state_dict = state.to_dict()
        try:
            response = tbl.update_item(
                Key={"name": state_dict["name"], "run_id": state_dict["run_id"]},
                UpdateExpression="set steps=:steps, cache=:cache",
                ExpressionAttributeValues={":steps": state_dict["steps"], ":cache": state_dict["cache"]},
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
        print(f"DEBUG: Type of name: {type(name)}, value: {name}")
        print(f"DEBUG: Type of table name: {type(tbl.table_name)}, value: {tbl.table_name}")
        response = tbl.query(
            KeyConditionExpression=Key('name').eq(name),
            ScanIndexForward=False,  
            Limit=1 
        )

        items = response.get('Items', [])
        latest_run_id = items[0]['run_id'] if items else 0
        return latest_run_id + 1


    def get_endpoint(self, name, component) -> str:
        '''
        Args ->

            name: The name of the workflow.
            component: One of SwitchboardComponent Enum (InvocationQueue, ExecutorQueue)

        Queries the SwitchboardResources table to retrieve the given component's url endpoint for the given workflow.
        '''
        tbl = self.get_table(TableName.SwitchboardResources)
        try:
            resp = tbl.get_item(Key={"component": component.value, "name": name})
            print(f"!!!!!! Retrieved item '{resp}'")
        except ClientError as err:
            print(f"!!!!!! Could not get resource for name={name}, component={component}")
            raise Exception(
                "%s - Couldn't get %s endpoint for %s from table %s. %s: %s",
                name,
                component,
                tbl.table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )

        item = resp.get("Item")
        if not item:
            raise Exception(f"No entry found for name={name}, component={component} in {tbl.table_name}")

        return item["url"]


    def get_table(self,table=TableName.SwitchboardState):
        tbl = self.conn.Table(table.value)
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





