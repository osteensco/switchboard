package core

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestInitProject(t *testing.T) {
	testCases := []struct {
		name            string
		lang            string
		cloud           string
		tf_vars         map[string]string
		expectedContent string
		expectedFiles   []string
	}{
		{
			name:    "Python",
			lang:    "py",
			cloud:   "aws",
			tf_vars: map[string]string{"switchboard_role_arn": "placeholder_arn"},
			expectedContent: `switchboard_role_arn = "placeholder_arn"
workflow_name = "my-test-project-py"
workflow_handler = "workflow.workflow_handler"
executor_handler = "executor.lambda_handler"
runtime = "python3.11"
`,
			expectedFiles: []string{
				".gitignore",
				"README.md",
				"iam_policy.json",
				"workflow/workflow.py",
				"workflow/requirements.txt",
				"executor/executor.py",
				"executor/tasks.py",
				"executor/requirements.txt",
				"terraform/main.tf",
				"terraform/variables.tf",
				"terraform/outputs.tf",
				"terraform/modules/lambda/main.tf",
			},
		},

		// {
		// 	name:  "TypeScript",
		// 	lang:  "ts",
		// 	cloud: "aws",
		// 	expectedContent: `workflow_name = "my-test-project-ts"
		// 	workflow_handler = "dist/workflow.workflow_handler"
		// 	workflow_runtime = "nodejs18.x"
		// 	executor_handler = "dist/executor.lambda_handler"
		// 	executor_runtime = "nodejs18.x"
		// 	`,
		// 	expectedFiles: []string{
		// 		"workflow/workflow.ts",
		// 		"workflow/package.json",
		// 		"executor/executor.ts",
		// 		"executor/tasks.ts",
		// 		"executor/package.json",
		// 	},
		// },
		// {
		// 	name:  "Go",
		// 	lang:  "go",
		// 	cloud: "aws",
		// 	expectedContent: `workflow_name = "my-test-project-go"
		// 	workflow_handler = "main"
		// 	workflow_runtime = "go1.x"
		// 	executor_handler = "main"
		// 	executor_runtime = "go1.x"
		// 	`,
		// 	expectedFiles: []string{
		// 		"workflow/workflow.go",
		// 		"workflow/go.mod",
		// 		"workflow/go.sum",
		// 		"executor/executor.go",
		// 		"executor/tasks.go",
		// 		"executor/go.mod",
		// 		"executor/go.sum",
		// 	},
		// },
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			// Create a temporary directory for the test
			tmpDir, err := os.MkdirTemp("", "test-project-")
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

			projectName := "my-test-project-" + tc.lang
			progress := make(chan ProgressUpdate)
			var initErr error

			go func() {
				for range progress {
					// Drain the channel
				}
			}()

			initErr = InitProject(projectName, tc.cloud, tc.lang, tc.tf_vars, progress)
			if initErr != nil {
				t.Fatalf("InitProject failed: %v", initErr)
			}

			// Check that the expected directories and files are created
			for _, file := range tc.expectedFiles {
				fullPath := filepath.Join(projectName, file)
				if _, err := os.Stat(fullPath); os.IsNotExist(err) {
					t.Errorf("Expected file or directory to exist: %s", fullPath)
				}
			}

			// Check the content of terraform.tfvars
			tformvarsPath := filepath.Join(projectName, "terraform", "terraform.tfvars")
			content, err := os.ReadFile(tformvarsPath)
			if err != nil {
				t.Fatal(err)
			}

			// Normalize line endings for comparison
			normalizedContent := strings.ReplaceAll(string(content), "\r\n", "\n")

			if normalizedContent != tc.expectedContent {
				t.Errorf("Expected terraform.tfvars content to be \n%s\nbut got \n%s", tc.expectedContent, normalizedContent)
			}
		})
	}
}
