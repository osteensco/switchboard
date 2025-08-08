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

func InitProject(name string, cloud string, lang string, tf_vars map[string]string, progress chan<- ProgressUpdate) error {
	defer close(progress)

	progress <- ProgressUpdate{Message: fmt.Sprintf("Creating project directory: %s", name)}
	projectName := name
	if err := os.Mkdir(projectName, 0755); err != nil {
		return fmt.Errorf("error creating project directory: %w", err)
	}

	progress <- ProgressUpdate{Message: "Creating subdirectories..."}
	workflowDir := filepath.Join(projectName, "workflow")
	executorDir := filepath.Join(projectName, "executor")
	terraformDir := filepath.Join(projectName, "terraform")
	for _, dir := range []string{workflowDir, executorDir, terraformDir} {
		if err := os.Mkdir(dir, 0755); err != nil {
			return fmt.Errorf("error creating subdirectory %s: %w", dir, err)
		}
	}

	progress <- ProgressUpdate{Message: "Copying template files..."}
	templateRoot := "templates"

	// Template files can be found in cli/src/assets/templates
	// We are building out a basic project for the user here, so we will generate:
	//	- Workflow source code
	//	- Executor source code
	//	- All required terraform
	// 	- Readme, gitignore, and supporting cloud assets like iam policies or service accounts

	// Copy language-specific files
	langTemplatePath := filepath.Join(templateRoot, cloud, lang)

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
	if err := copyFiles(filepath.Join(templateRoot, cloud), projectName); err != nil {
		return fmt.Errorf("error copying generic files: %w", err)
	}

	// Copy terraform
	terraformTemplatePath := filepath.Join(templateRoot, cloud, "terraform")
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

	templatePath := filepath.Join(templateRoot, cloud, "terraform", "terraform.tfvars.tmpl")
	tmpl, err := template.ParseFS(assets.Templates, templatePath)
	if err != nil {
		return fmt.Errorf("error parsing template: %w", err)
	}
	defer os.Remove(templatePath)

	// Fill out terraform variables based on the user's input for the new project
	data := TfvarsData{WorkflowName: name, Language: lang, CloudTfVars: tf_vars}
	if err := tmpl.Execute(tformvarsFile, data); err != nil {
		return fmt.Errorf("error executing template: %w", err)
	}

	// Create switchboard.json
	progress <- ProgressUpdate{Message: "Creating switchboard.json..."}
	config := ProjectConfig{
		Name:     name,
		Language: lang,
		Cloud:    cloud,
	}
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

func AddTrigger(trigger string) {
	// TODO implement different out-of-the-box triggers
	fmt.Println("Trigger added: " + trigger)
}
