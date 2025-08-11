package core

import (
	"fmt"
	"os"
	"path/filepath"
)

var PackageFuncs = func(progress chan<- ProgressUpdate) error {
	defer close(progress)

	config, projectRoot, err := loadConfig()
	if err != nil {
		progress <- ProgressUpdate{Message: err.Error()}
		return err
	}

	progress <- ProgressUpdate{Message: "Packaging serverless functions for deployment..."}

	if err := packageComponent("workflow", config, projectRoot, progress); err != nil {
		return fmt.Errorf("error packaging workflow: %w", err)
	}

	if err := packageComponent("executor", config, projectRoot, progress); err != nil {
		return fmt.Errorf("error packaging executor: %w", err)
	}

	progress <- ProgressUpdate{Message: "Packaging complete."}
	return nil
}

func DeployWorkflow(progress chan<- ProgressUpdate) error {
	defer close(progress)

	config, projectRoot, err := loadConfig()
	if err != nil {
		progress <- ProgressUpdate{Message: err.Error()}
		return err
	}

	progress <- ProgressUpdate{Message: "Verifying project is packaged for deployment..."}

	// Get cloud specific terraform information and verify package operation output exists
	env := os.Environ()
	switch config.Cloud {
	case "aws":

		workflow_path := filepath.Join(projectRoot, "workflow")
		if _, err := os.Stat(workflow_path); os.IsNotExist(err) {
			progress <- ProgressUpdate{Message: "Project not properly packaged for deployment!"}
			return err
		}
		zipFilePath := filepath.Join(workflow_path, "workflow_lambda.zip")
		if _, err := os.Stat(zipFilePath); os.IsNotExist(err) {
			progress <- ProgressUpdate{Message: "Project not properly packaged for deployment!"}
			return err
		}

		executor_path := filepath.Join(projectRoot, "executor")
		if _, err := os.Stat(executor_path); os.IsNotExist(err) {
			progress <- ProgressUpdate{Message: "Project not properly packaged for deployment!"}
			return err
		}
		zipFilePath = filepath.Join(executor_path, "executor_lambda.zip")
		if _, err := os.Stat(zipFilePath); os.IsNotExist(err) {
			progress <- ProgressUpdate{Message: "Project not properly packaged for deployment!"}
			return err
		}

		arn, err := getArn(progress)
		if err != nil {
			return err
		}
		env = append(env, "TF_VAR_switchboard_role_arn="+arn)
	}

	progress <- ProgressUpdate{Message: "Initializing and applying Terraform..."}

	terraformDir := filepath.Join(projectRoot, "terraform")

	initCmd := execCommand("terraform", "init")
	initCmd.Dir = terraformDir
	initCmd.Stdout = os.Stdout
	initCmd.Stderr = os.Stderr
	initCmd.Env = env
	if err := initCmd.Run(); err != nil {
		progress <- ProgressUpdate{Message: fmt.Sprintf("Error running terraform init: %v", err)}
		return fmt.Errorf("error running terraform init: %w", err)
	}

	validateCmd := execCommand("terraform", "validate")
	validateCmd.Dir = terraformDir
	validateCmd.Stdout = os.Stdout
	validateCmd.Stderr = os.Stderr
	validateCmd.Env = env
	if err := validateCmd.Run(); err != nil {
		progress <- ProgressUpdate{Message: fmt.Sprintf("Error running terraform validate: %v", err)}
		return fmt.Errorf("error running terraform init: %w", err)
	}

	applyCmd := execCommand("terraform", "apply", "-auto-approve")
	applyCmd.Dir = terraformDir
	applyCmd.Stdout = os.Stdout
	applyCmd.Stderr = os.Stderr
	applyCmd.Env = env
	if err := applyCmd.Run(); err != nil {
		progress <- ProgressUpdate{Message: fmt.Sprintf("Error running terraform apply: %v", err)}
		return fmt.Errorf("error running terraform apply: %w", err)
	}

	progress <- ProgressUpdate{Message: "Workflow deployed successfully."}
	return nil
}

func TeardownWorkflow(progress chan<- ProgressUpdate) error {
	defer close(progress)

	config, projectRoot, err := loadConfig()
	if err != nil {
		progress <- ProgressUpdate{Message: err.Error()}
		return err
	}

	env := os.Environ()
	switch config.Cloud {
	case "aws":
		arn, err := getArn(progress)
		if err != nil {
			return err
		}
		env = append(env, "TF_VAR_switchboard_role_arn="+arn)
	}

	progress <- ProgressUpdate{Message: "Tearing down workflow components..."}

	terraformDir := filepath.Join(projectRoot, "terraform")

	destroyCmd := execCommand("terraform", "destroy", "-auto-approve")
	destroyCmd.Dir = terraformDir
	destroyCmd.Stdout = os.Stdout
	destroyCmd.Stderr = os.Stderr
	destroyCmd.Env = env
	if err := destroyCmd.Run(); err != nil {
		progress <- ProgressUpdate{Message: fmt.Sprintf("Error running terraform destroy: %v", err)}
		return fmt.Errorf("error running terraform destroy: %w", err)
	}

	progress <- ProgressUpdate{Message: "Workflow components purged from the cloud."}
	return nil
}
