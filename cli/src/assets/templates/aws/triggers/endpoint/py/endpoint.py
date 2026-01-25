# TODO 
#   implement me


# - find invocation queue from Switchboard Resources table
# - create trigger object
# - capture response?


from switchboard import Trigger, Cloud, DB

def enpoint_handler(event, context):
    db = DB(Cloud.AWS)
    workflow_name = "myworkflow" # TODO: We should grab workflow name from the project's switchboard.json and autopopulate it here.
    workflow_trigger = Trigger(cloud=Cloud.AWS, db=db.interface, name=workflow_name)
    
    return "success"
