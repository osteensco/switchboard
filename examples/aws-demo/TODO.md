# Dev plan for the aws-demo

 - [ ] dependencies installed into dist:
    - reevalute this strategy for ensuring dependencies are included on switchboard component creation
    - the current folder structure for the lambdas does not look super clean and leads to weird imports like `from src.tasks import directory_map`

 - [ ] workflow name should be attached to the deployed components (ie myworkflow-executor)
    - database would be excluded from this as it would be more efficient for global db in a project

 - [x] database tables don't need to be repeated, but need to ensure schema allows for this

 - [ ] consolidate into a single log group to ensure logs are coherent across the various switchboard componenets
    - the focus here is the developer experience trying to parse logs and debug pipelines

 - [ ] If a user creates a custom DBInterface, this would need to be included in the workflow and executor functions.
    - This means that a custom DBInterface should probably be added in a separate .py file and imported in both workflow and executor function files.
    - Need to account for this in documentation and the cli tool's deployer.

