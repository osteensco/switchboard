# Switchboard CLI Development Plan

This document outlines the plan for building the `switchboard` CLI tool. 
The goal is to provide a user-friendly interface for initializing, building, and deploying Switchboard projects.

## Core Commands
 - [ ] **Scaffolder**
    - [x] **`sb new`**
        - **Purpose:** To scaffold a new Switchboard project directory.
        - **Actions:**
            - Generate the following files from templates:
                - `workflow`
                - `executor`
                - `tasks`
                - `trigger/..` (all necessary trigger related source code)
                - `terraform/...` (all necessary `.tf` files)
                - `requirements.txt` (or equivalent)
                - `README.md` (with instructions for the user)
                - `.gitignore`

    - [ ] **`sb add trigger <trigger_type>`**
        **NOTE:** Trigger addition should be in project setup phase as well
        - **Purpose:** Provide out-of-the-box trigger components for initiating workflows. 
            - Four types of triggers, and the option to implement a custom trigger using the sdk:
                - Endpoint
                - Cron
                - Event Listener
                - Queue subscriber
                - Custom
        - **Actions:**
            - Maps `trigger_type` to predefined terraform scripts
            - Adds these terraform scripts to project's terraform directory
            - Adds the trigger component to the SwitchboardResources table if the db exists.
        - **Notes:**
            - Out-of-the-box triggers won't cover all use cases, but hopefully cover more common ones.
            - Custom added triggers
                - Triggers need a way to be added to the SwitchboardResources table manually

    - [ ] **`sb tidy`**
        - **Purpose:** Fix terraform scripts if custom resources were created after the fact
            - This should mainly only apply to updating the tf portion that seeds the SwitchboardResources table in the database.
        - **Actions:**
            - TODO: figure out what actions would need to be taken exactly

 - [x] **Deployer**
    - [x] **`sb package`**
        - **Purpose:** To create the `lambda_package.zip` deployment artifact.
        - **Actions:**
            - Verify workflow and executor directories exist.
            - For workflow and executor each:
                - Create a temporary build directory.
                - Copy source code into build directory.
                - Install all dependencies from `requirements.txt` (or equivalent) into the build directory.
                - Zip the contents of the build directory into a `*_lambda.zip` file.

    - [x] **`sb deploy`**
        - **Purpose:** To abstract `terraform apply` and deploy the project to the cloud.
        - **Actions:**
            - Read project configuration (e.g., `project_name`, `environment`) from a config file (e.g., `switchboard.toml`).
            - Run `terraform init` and `terraform apply` in the `terraform/` directory, passing in the necessary variables.
            - Populate the SwitchboardResources table with the deployed components.

    - [x] **`sb teardown`**
        - **Purpose:** To abstract `terraform destroy` and tear down all cloud resources.
        - **Actions:**
            - Run `terraform destroy` in the `terraform/` directory.
            - Remove everything created with the `sb package` command.

 - [ ] **Logs Viewer**
    - [ ] **`sb logs <workflow name> <query string>`**
        - **Purpose:** Queries logs and displays results to the user.
        - **Actions:**
            - Queries SwitchBoard resources table for given workflow's log sink.
            - Passes provided query string to log sink or pulls down last 100 log entries if no query provided.
            - Displays queried logs to user.


------The specific sub commands for these need to be defined-------
 - [ ] **Components**
    - [ ] `sb component <command> <args>`
        - **Purpose:** Provide component info to the user.
        - **Actions:**
            - Discover SwitchBoard resources that are deployed.
            - Display information to the user.

 - [ ] **Workflows**
    - [ ] `sb workflow <command> <args>`
        - **Purpose:** Interact with specific workflows.
        - **Actions:**
            - View Workflow runs and states.
            - Manual trigger, retry, pause, stop, state change, etc of workflows.
    - [ ] `sb workflow trigger <workflow name>`
        - **Purpose:** Trigger the designated workflow. Attepmts to trigger the workflow of the current project if no workflow name is provided.
        - **Actions:**
            - Query Database for given workflow's invocation queue.
            - Push preconfigured message to invocation queue to initialize a new workflow.
        

## Testing

 - [ ] Add dockerfile that executes a new project creation, deployment, and cleanup
    - Needs a new subdir in test_env or another folder entirely for integration tests
    - Need a way to handle cleanup on failures (`terraform destroy` isn't necessarily going to work on all failures)


## Docs

 - [ ] A 'Contributing' doc needs to be added with a section on how to run tests and what make commands are available.
 - [ ] Migrate "examples" directory to a quickstart example using the cli tool and default templated project.

## DB Schema

 - **SwitchboardResources:**
    - [ ] Update "name" field to "workflow_name"
        - **IMPORTANT:** This requires updating the SDK
    - [ ] Update "url" field to be more descriptive (could be endpoint url, function name, or something else)
        - Alternatives: "id", "uri", "ref", "handle"
        - **IMPORTANT:** This may require updating the SDK

## Code Quality

 - **Implement enums for:**
    -- May be unnecessary --
    - [ ] SDK language
    - [ ] Cloud provider
    - [ ] Trigger type

## Configuration

 - [x] A project-level configuration file (e.g.,`switchboard.json` or `switchboard.toml`) will be generated by `new` to store metadata like `project_name` and `environment`. 
This file will be read by the `deploy` command.

## Templates
 - [x] Templates should have language directories for each cloud 

```
templates
    ├── aws
    │   ├── py
    │   │   ├── executor.py
    │   │   ├── tasks.py
    │   │   ├── workflow.py
    │   │   └── requirements.txt
    │   ├── ts
    │   │   ├── executor.ts
    │   │   ├── tasks.ts
    │   │   ├── workflow.ts
    │   │   └── package.json
    │   ├── go
    │   │   ├── executor.go
    │   │   ├── tasks.go
    │   │   ├── workflow.go
    │   │   ├── go.mod
    │   │   └── go.sum
    │   ├── .gitignore
    │   ├── iam_policy.json
    │   ├── README.md
    │   └── terraform/
    ├── gcp
    └── azure
```

 - [x] Project structure after running `sb new` and `sb package` commands should look like this -

```
[project root]
   ├── executor
   │   ├── `.dist`
   │   ├── `executor_lambda.zip`
   │   ├── executor.py
   │   ├── tasks.py
   │   └── requirements.txt
   ├── workflow
   │   ├── `.dist`
   │   ├── `workflow_lambda.zip`
   │   ├── workflow.py
   │   └── requirements.txt
   ├── trigger (endpoint trigger shown here)
   │   ├── `.dist`
   │   ├── `endpoint_lambda.zip`
   │   ├── endpoint.py
   │   └── requirements.txt
   ├── .gitignore
   ├── iam_policy.json
   ├── README.md
   └── terraform/
```


## Product Notes
  - Most orgs are going to have their own devops pipelines. 
    switchboard should provide terraform, jenkins, and CDK scripts that enable users to integrate easily into their own abstractions.
  - Log sinks should be set up in such a way to easily utilize third party observability tools.





