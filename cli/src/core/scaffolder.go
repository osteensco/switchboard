package core

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"

	"github.com/osteensco/switchboard/cli/assets"
)

func InitProject(name string, cloud string, lang string) {
	// Create project directory
	projectName := name
	err := os.Mkdir(projectName, 0755)
	if err != nil {
		fmt.Println("Error creating project directory:", err)
		return
	}

	// Create workflow and executor directories
	workflowDir := filepath.Join(projectName, "workflow")
	executorDir := filepath.Join(projectName, "executor")

	err = os.Mkdir(workflowDir, 0755)
	if err != nil {
		fmt.Println("Error creating workflow directory:", err)
		return
	}

	err = os.Mkdir(executorDir, 0755)
	if err != nil {
		fmt.Println("Error creating executor directory:", err)
		return
	}

	// Copy template files
	templateRoot := "templates"

	// Copy generic files
	copyTemplates(filepath.Join(templateRoot, cloud), projectName, func(path string) bool {
		return !strings.Contains(path, "/")
	})

	// Copy language-specific files
	langTemplatePath := filepath.Join(templateRoot, cloud, lang)
	copyTemplates(langTemplatePath, projectName, nil)

	// Copy terraform directory
	terraformTemplatePath := filepath.Join(templateRoot, cloud, "terraform")
	copyTemplates(terraformTemplatePath, filepath.Join(projectName, "terraform"), nil)

	// Create terraform.tfvars
	tformvarsContent := fmt.Sprintf("workflow_name = \"%s\"\n", name)
	switch lang {
	case "py":
		tformvarsContent += "workflow_handler = \"src.workflow.workflow_handler\"\n"
		tformvarsContent += "workflow_runtime = \"python3.11\"\n"
		tformvarsContent += "executor_handler = \"src.executor.lambda_handler\"\n"
		tformvarsContent += "executor_runtime = \"python3.11\"\n"
	case "ts":
		tformvarsContent += "workflow_handler = \"dist/workflow.workflow_handler\"\n"
		tformvarsContent += "workflow_runtime = \"nodejs18.x\"\n"
		tformvarsContent += "executor_handler = \"dist/executor.lambda_handler\"\n"
		tformvarsContent += "executor_runtime = \"nodejs18.x\"\n"
	case "go":
		tformvarsContent += "workflow_handler = \"main\"\n"
		tformvarsContent += "workflow_runtime = \"go1.x\"\n"
		tformvarsContent += "executor_handler = \"main\"\n"
		tformvarsContent += "executor_runtime = \"go1.x\"\n"
	}

	tformvarsPath := filepath.Join(projectName, "terraform", "terraform.tfvars")
	err = os.WriteFile(tformvarsPath, []byte(tformvarsContent), 0644)
	if err != nil {
		fmt.Println("Error creating terraform.tfvars:", err)
		return
	}

	fmt.Println("Project created successfully!")
}

func copyTemplates(templatePath, destPath string, filter func(path string) bool) error {
	return fs.WalkDir(assets.Templates, templatePath, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		if filter != nil && !filter(path) {
			return nil
		}

		// Create the destination path
		dest := filepath.Join(destPath, path[len(templatePath):])

		if d.IsDir() {
			return os.MkdirAll(dest, 0755)
		} else {
			content, err := assets.Templates.ReadFile(path)
			if err != nil {
				return err
			}
			return os.WriteFile(dest, content, 0644)
		}
	})
}

func AddTrigger(trigger string) {
	fmt.Println("Trigger added: " + trigger)
}
