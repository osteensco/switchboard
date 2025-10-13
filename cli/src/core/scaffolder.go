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

	projectDir := projectPaths{
		Workflow:  filepath.Join(projectName, "workflow"),
		Executor:  filepath.Join(projectName, "executor"),
		Terraform: filepath.Join(projectName, "terraform"),
		Trigger:   filepath.Join(projectName, "trigger"),
	}

	// Create all project directories
	if err := os.Mkdir(projectDir.Workflow, 0755); err != nil {
		return fmt.Errorf("error creating subdirectory %s: %w", projectDir.Workflow, err)
	}
	if err := os.Mkdir(projectDir.Executor, 0755); err != nil {
		return fmt.Errorf("error creating subdirectory %s: %w", projectDir.Executor, err)
	}
	if err := os.Mkdir(projectDir.Terraform, 0755); err != nil {
		return fmt.Errorf("error creating subdirectory %s: %w", projectDir.Terraform, err)
	}
	if err := os.Mkdir(projectDir.Trigger, 0755); err != nil {
		return fmt.Errorf("error creating subdirectory %s: %w", projectDir.Trigger, err)
	}

	progress <- ProgressUpdate{Message: "Copying template files..."}

	// Template files can be found in cli/src/assets/templates
	// We are building out a basic project for the user here, so we will generate:
	//	- Trigger source code (if applicable)
	//	- Workflow source code
	//	- Executor source code
	//	- All required terraform
	// 	- Readme, gitignore, and supporting cloud assets like iam policies or service accounts

	templateDir := templatePaths{
		Root:      "templates",
		Language:  filepath.Join("templates", config.Cloud, config.Language),
		Terraform: filepath.Join("templates", config.Cloud, "terraform"),
		Triggers:  filepath.Join("templates", config.Cloud, "triggers"),
	}

	// Copy necessary trigger related files
	AddTrigger(projectDir, templateDir, config, progress)

	// Copy workflow files
	if err := copyFiles(templateDir.Language, projectDir.Workflow); err != nil {
		return fmt.Errorf("error copying workflow files: %w", err)
	}
	if err := copyFiles(filepath.Join(templateDir.Language, "workflow"), projectDir.Workflow); err != nil {
		return fmt.Errorf("error copying workflow files: %w", err)
	}

	// Copy executor files
	if err := copyFiles(templateDir.Language, projectDir.Executor); err != nil {
		return fmt.Errorf("error copying executor files: %w", err)
	}
	if err := copyFiles(filepath.Join(templateDir.Language, "executor"), projectDir.Executor); err != nil {
		return fmt.Errorf("error copying workflow files: %w", err)
	}

	// Copy generic root files
	if err := copyFiles(filepath.Join(templateDir.Root, config.Cloud), projectName); err != nil {
		return fmt.Errorf("error copying generic files: %w", err)
	}

	// Copy terraform
	if err := copyDirectory(templateDir.Terraform, projectDir.Terraform); err != nil {
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

	templatePath := filepath.Join(templateDir.Root, config.Cloud, "terraform", "terraform.tfvars.tmpl")
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

func AddTrigger(projectDir projectPaths, templateDir templatePaths, config ProjectConfig, progress chan<- ProgressUpdate) error {

	var err error
	progress <- ProgressUpdate{Message: "Implementing Trigger..."}

	if config.Trigger == "custom" {
		// Enable custom trigger
		// TODO: what info is needed to add trigger to SwitchboardResources table?
	}
	switch config.Cloud {
	case "aws":
		err = createAWSTrigger(projectDir, templateDir, config)
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

func createAWSTrigger(projectDir projectPaths, templateDir templatePaths, config ProjectConfig) error {
	switch config.Trigger {
	case "endpoint":
		// copy necessary source code
		sourcecodePath := filepath.Join(templateDir.Triggers, config.Trigger, config.Language)
		// TODO - may need to end up using copyDirectory here instead
		if err := copyFiles(sourcecodePath, projectDir.Trigger); err != nil {
			return fmt.Errorf("error copying trigger source code files: %w", err)
		}

		// copy appropriate terraform
		terraformPath := filepath.Join(templateDir.Triggers, config.Trigger)
		triggerTfPath := filepath.Join(projectDir.Terraform, "modules", "trigger")
		if err := copyFiles(terraformPath, triggerTfPath); err != nil {
			return fmt.Errorf("error copying trigger's terraform files: %w", err)
		}

	case "cron":
	case "listener":
	case "subscribrer":
	default:
		return fmt.Errorf("Invalid trigger type provided: '%s'", config.Trigger)
	}
	return nil
}

// TODO
//	- teardown functions for triggers? (and other components)

func createGCPTrigger(config ProjectConfig) error {
	return nil
}

func createAzureTrigger(config ProjectConfig) error {
	return nil
}
