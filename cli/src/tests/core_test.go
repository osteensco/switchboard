package test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/osteensco/switchboard/cli/core"
)

func TestInitProject(t *testing.T) {
	// Create a temporary directory for the test
	tmpDir, err := os.MkdirTemp("", "test-project")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(tmpDir)

	// Change to the temporary directory
	originalDir, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	defer os.Chdir(originalDir)
	os.Chdir(tmpDir)

	// Call InitProject with test data
	projectName := "my-test-project"
	cloud := "aws"
	lang := "py"
	core.InitProject(projectName, cloud, lang)

	// Check that the expected directories and files are created
	expectedFiles := []string{
		filepath.Join(projectName, "workflow"),
		filepath.Join(projectName, "executor"),
		filepath.Join(projectName, "terraform"),
		filepath.Join(projectName, "terraform", "terraform.tfvars"),
	}

	for _, file := range expectedFiles {
		if _, err := os.Stat(file); os.IsNotExist(err) {
			t.Errorf("Expected file or directory to exist: %s", file)
		}
	}

	// Check the content of terraform.tfvars
	tformvarsPath := filepath.Join(projectName, "terraform", "terraform.tfvars")
	content, err := os.ReadFile(tformvarsPath)
	if err != nil {
		t.Fatal(err)
	}

	expectedContent := `workflow_name = "my-test-project"
workflow_handler = "src.workflow.workflow_handler"
workflow_runtime = "python3.11"
executor_handler = "src.executor.lambda_handler"
executor_runtime = "python3.11"
`
	if string(content) != expectedContent {
		t.Errorf("Expected terraform.tfvars content to be '%s', but got '%s'", expectedContent, string(content))
	}
}
