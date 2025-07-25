# Switchboard CLI Development Plan

This document outlines the plan for building the `switchboard` CLI tool. The goal is to provide a user-friendly interface for initializing, building, and deploying Switchboard projects.

## Core Commands

- [ ] **`switchboard init <project_name>`**
    - **Purpose:** To scaffold a new Switchboard project directory.
    - **Actions:**
        - Create a new directory with the given project name or scaffold current working directory if not project_name provided.
        - Generate the following files from templates:
            - `src/switchboard.py`
            - `src/executor.py`
            - `src/tasks.py`
            - `terraform/...` (all necessary `.tf` files)
            - `requirements.txt` (Dynamically generated at runtime to specify the `switchboard-sdk` version and other dependencies for the Lambda package)
            - `README.md` (with instructions for the user)
            - `.gitignore`

- [ ] **`switchboard add <trigger_type>`**
    - **Purpose**: Provide out-of-the-box trigger components for initiating workflows. (Cron, http endpoints, etc.)
    - **Actions:**
        - Maps `trigger_type` to predefined terraform scripts
        - Adds these terraform scripts to project's terraform directory

- [ ] **`switchboard package`**
    - **Purpose:** To create the `lambda_package.zip` deployment artifact.
    - **Actions:**
        - Create a temporary build directory.
        - Install all dependencies from `requirements.txt` into the build directory.
        - Copy the user's source code from the `src/` directory.
        - Zip the contents of the build directory into a `lambda_package.zip` file in the `terraform/` directory.

- [ ] **`switchboard deploy`**
    - **Purpose:** To abstract `terraform apply` and deploy the project to the cloud.
    - **Actions:**
        - Read project configuration (e.g., `project_name`, `environment`) from a config file (e.g., `switchboard.toml`).
        - Run `terraform init` and `terraform apply` in the `terraform/` directory, passing in the necessary variables.

- [ ] **`switchboard destroy`**
    - **Purpose:** To abstract `terraform destroy` and tear down all cloud resources.
    - **Actions:**
        - Run `terraform destroy` in the `terraform/` directory.

## Configuration

- [ ] A project-level configuration file (e.g., `switchboard.toml`) will be generated by `init` to store metadata like `project_name` and `environment`. This file will be read by the `deploy` command.
