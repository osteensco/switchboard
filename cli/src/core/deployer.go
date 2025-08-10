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

	progress <- ProgressUpdate{Message: "Initializing and applying Terraform..."}

	projectRoot, err := findProjectRoot()
	if err != nil {
		return err
	}
	config, projectRoot, err := loadConfig()
	if err != nil {
		progress <- ProgressUpdate{Message: err.Error()}
		return err
	}
	// Get cloud specific terraform information
	env := os.Environ()
	switch config.Cloud {
	// alternative to running -
	// 		export TF_VAR_switchboard_role_arn=$(aws iam get-role --role-name switchboard-role --query 'Role.Arn' --output text)
	case "aws":
		arn, err := getArn(progress)
		if err != nil {
			return err
		}
		env = append(env, "TF_VAR_switchboard_role_arn="+arn)
	}

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

	// TODO
	//	- auto-approve will cause issues here, need to ensure it's interactive instead. This interactivity will have to be managed by each UI package.
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

	progress <- ProgressUpdate{Message: "Tearing down workflow components..."}

	projectRoot, err := findProjectRoot()
	if err != nil {
		return err
	}

	terraformDir := filepath.Join(projectRoot, "terraform")

	destroyCmd := execCommand("terraform", "destroy", "-auto-approve")
	destroyCmd.Dir = terraformDir
	destroyCmd.Stdout = os.Stdout
	destroyCmd.Stderr = os.Stderr
	if err := destroyCmd.Run(); err != nil {
		progress <- ProgressUpdate{Message: fmt.Sprintf("Error running terraform destroy: %v", err)}
		return fmt.Errorf("error running terraform destroy: %w", err)
	}

	progress <- ProgressUpdate{Message: "Workflow components purged from the cloud."}
	return nil
}
