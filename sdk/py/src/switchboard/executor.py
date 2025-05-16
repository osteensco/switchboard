from switchboard.invocation import Invoke



# The switchboard executor function will be wrapped in a simple serverless function call as demonstrated below.
#
#   def lambda_handler(event, context):
#       return switchboard_executor(context)
#
#   

# The executor's queue should be an internal implementation always (no custom queue)



def switchboard_execute(context):
    pass


def push_to_executor(cloud, body) -> dict:
    # get endpoint from db?
    ep = ""

    response = Invoke(cloud, ep, body)
    return response



