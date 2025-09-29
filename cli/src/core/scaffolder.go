package core

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"text/template"

	"github.com/osteensco/switchboard/cli/assets"
)

type TfvarsData struct {
	WorkflowName string
	Language     string
	CloudTfVars  map[string]string
}

func InitProject(config ProjectConfig, progress chan<- ProgressUpdate) error {
	// TODO
	//	- ensure idempotency
	//	- break down into smaller functions so individual portions can be rebuilt
	//		- renaming project, changing desired trigger, migrating to a different cloud, etc.
	defer close(progress)

	progress <- ProgressUpdate{Message: fmt.Sprintf("Creating project directory: %s", config.Name)}
	projectName := config.Name
	if err := os.Mkdir(projectName, 0755); err != nil {
		return fmt.Errorf("error creating project directory: %w", err)
	}

	progress <- ProgressUpdate{Message: "Creating subdirectories..."}

	workflowDir := filepath.Join(projectName, "workflow")
	executorDir := filepath.Join(projectName, "executor")
	terraformDir := filepath.Join(projectName, "terraform")
	triggerDir := filepath.Join(projectName, "trigger")
	for _, dir := range []string{workflowDir, executorDir, terraformDir, triggerDir} {
		if err := os.Mkdir(dir, 0755); err != nil {
			return fmt.Errorf("error creating subdirectory %s: %w", dir, err)
		}
	}

	AddTrigger(config, progress)

	progress <- ProgressUpdate{Message: "Copying template files..."}
	templateRoot := "templates"

	// Template files can be found in cli/src/assets/templates
	// We are building out a basic project for the user here, so we will generate:
	//	- Workflow source code
	//	- Executor source code
	//	- Trigger source code (if applicable)
	//	- All required terraform
	// 	- Readme, gitignore, and supporting cloud assets like iam policies or service accounts

	// Copy language-specific files
	langTemplatePath := filepath.Join(templateRoot, config.Cloud, config.Language)

	// Copy workflow files
	if err := copyFiles(langTemplatePath, workflowDir); err != nil {
		return fmt.Errorf("error copying workflow files: %w", err)
	}
	if err := copyFiles(filepath.Join(langTemplatePath, "workflow"), workflowDir); err != nil {
		return fmt.Errorf("error copying workflow files: %w", err)
	}

	// Copy executor files
	if err := copyFiles(langTemplatePath, executorDir); err != nil {
		return fmt.Errorf("error copying executor files: %w", err)
	}
	if err := copyFiles(filepath.Join(langTemplatePath, "executor"), executorDir); err != nil {
		return fmt.Errorf("error copying workflow files: %w", err)
	}

	// Copy generic root files
	if err := copyFiles(filepath.Join(templateRoot, config.Cloud), projectName); err != nil {
		return fmt.Errorf("error copying generic files: %w", err)
	}

	// Copy terraform
	terraformTemplatePath := filepath.Join(templateRoot, config.Cloud, "terraform")
	if err := copyDirectory(terraformTemplatePath, terraformDir); err != nil {
		return fmt.Errorf("error copying terraform files: %w", err)
	}

	// Create terraform.tfvars
	progress <- ProgressUpdate{Message: "Creating terraform.tfvars..."}
	tformvarsPath := filepath.Join(projectName, "terraform", "terraform.tfvars")
	tformvarsFile, err := os.Create(tformvarsPath)
	if err != nil {
		return fmt.Errorf("error creating terraform.tfvars: %w", err)
	}
	defer tformvarsFile.Close()

	templatePath := filepath.Join(templateRoot, config.Cloud, "terraform", "terraform.tfvars.tmpl")
	tmpl, err := template.ParseFS(assets.Templates, templatePath)
	if err != nil {
		return fmt.Errorf("error parsing template: %w", err)
	}
	defer os.Remove(templatePath)

	// Fill out terraform variables based on the user's input for the new project
	data := TfvarsData{WorkflowName: config.Name, Language: config.Language}
	if err := tmpl.Execute(tformvarsFile, data); err != nil {
		return fmt.Errorf("error executing template: %w", err)
	}

	// Create switchboard.json
	progress <- ProgressUpdate{Message: "Creating switchboard.json..."}
	configData, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return fmt.Errorf("error marshalling config: %w", err)
	}
	configPath := filepath.Join(projectName, "switchboard.json")
	if err := os.WriteFile(configPath, configData, 0644); err != nil {
		return fmt.Errorf("error writing switchboard.json: %w", err)
	}

	// Send success message to mark completion
	progress <- ProgressUpdate{Message: "Project created successfully!"}
	return nil
}

func AddTrigger(config ProjectConfig, progress chan<- ProgressUpdate) error {

	var err error
	progress <- ProgressUpdate{Message: "Implementing Trigger..."}

	if config.Trigger == "custom" {
		// Enable custom trigger
		// TODO: what info is needed to add trigger to SwitchboardResources table?
	}
	switch config.Cloud {
	// copy appropriate terraform
	// copy necessary source code
	case "aws":
		err = createAWSTrigger(config)
	case "gcp":
		err = createGCPTrigger(config)
	case "azure":
		err = createAzureTrigger(config)
	default:
		err = fmt.Errorf("Invalid cloud provided: '%s'", config.Cloud)
	}
	if err != nil {
		return err
	}

	progress <- ProgressUpdate{Message: "Trigger added: " + config.Trigger}

	return nil
}

func createAWSTrigger(config ProjectConfig) error {
	switch config.Trigger {
	// copy appropriate terraform
	// copy necessary source code
	case "endpoint":
		// TODO - implement me :)
	case "cron":
	case "listener":
	case "subscribrer":
	default:
		return fmt.Errorf("Invalid trigger type provided: '%s'", config.Trigger)
	}
	return nil
}

func createGCPTrigger(config ProjectConfig) error {
	return nil
}

func createAzureTrigger(config ProjectConfig) error {
	return nil
}
