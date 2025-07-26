# Dev plan for the python sdk

 - [x] create separate requirements.txt (or equivalent) for production use vs sdk internal development (already defined in pyproject.toml)

 - [x] reevaluate chosen names (i.e. directory_map, Response, Invoke, etc)

 - [x] add status to SwitchboardState schema

 - [x] add retry argument to Call and ParallelCall

 - [ ] add additional libraries to enhance testing (moto, coverage)

 - [ ] add docker containers to test example locally

 - [x] address TODO notes throughout SDK

 - [x] convert print statements to log statements

 - [ ] Potential out-of-the-box tasks switchboard should provide
   - [ ] call http endpoint
   - [ ] trigger specific compute resources
   - [ ] push to message queue
   - [ ] trigger storage/DB operation (i.e. scheduled query or stored procedure)
   - [ ] trigger ML/Data Pipeline 
   - [ ] Event emitter/bus

