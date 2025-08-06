package core

import (
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"slices"
	"testing"
)

func TestPackageFuncs(t *testing.T) {
	// Save original functions and restore them after the test
	originalLoadConfig := loadConfig
	originalPackageComponent := packageComponent
	defer func() {
		loadConfig = originalLoadConfig
		packageComponent = originalPackageComponent
	}()

	testCases := []struct {
		name string
		setupMocks func()
		expectedErr error
		expectedProgress []string
	}{
		{
			name: "Successful Packaging",
			setupMocks: func() {
				loadConfig = func() (*ProjectConfig, string, error) {
					return &ProjectConfig{Name: "test", Language: "py", Cloud: "aws"}, "/tmp/test-project", nil
				}
				packageComponent = func(componentName string, config *ProjectConfig, projectRoot string, progress chan<- ProgressUpdate) error {
					progress <- ProgressUpdate{Message: "Component " + componentName + " packaged."}
					return nil
				}
			},
			expectedErr: nil,
			expectedProgress: []string{
				"Packaging serverless functions for deployment...",
				"Component workflow packaged.",
				"Component executor packaged.",
				"Packaging complete.",
			},
		},
		{
			name: "LoadConfig Error",
			setupMocks: func() {
				loadConfig = func() (*ProjectConfig, string, error) {
					return nil, "", errors.New("config error")
				}
				packageComponent = func(componentName string, config *ProjectConfig, projectRoot string, progress chan<- ProgressUpdate) error {
					return nil // Should not be called
				}
			},
			expectedErr: errors.New("config error"),
			expectedProgress: []string{
				"config error",
			},
		},
		{
			name: "Workflow Package Error",
			setupMocks: func() {
				loadConfig = func() (*ProjectConfig, string, error) {
					return &ProjectConfig{Name: "test", Language: "py", Cloud: "aws"}, "/tmp/test-project", nil
				}
				packageComponent = func(componentName string, config *ProjectConfig, projectRoot string, progress chan<- ProgressUpdate) error {
					if componentName == "workflow" {
						return errors.New("workflow package error")
					}
					return nil
				}
			},
			expectedErr: errors.New("error packaging workflow: workflow package error"),
			expectedProgress: []string{
				"Packaging serverless functions for deployment...",
			},
		},
		{
			name: "Executor Package Error",
			setupMocks: func() {
				loadConfig = func() (*ProjectConfig, string, error) {
					return &ProjectConfig{Name: "test", Language: "py", Cloud: "aws"}, "/tmp/test-project", nil
				}
				packageComponent = func(componentName string, config *ProjectConfig, projectRoot string, progress chan<- ProgressUpdate) error {
					if componentName == "executor" {
						return errors.New("executor package error")
					}
					progress <- ProgressUpdate{Message: "Component " + componentName + " packaged."}
					return nil
				}
			},
			expectedErr: errors.New("error packaging executor: executor package error"),
			expectedProgress: []string{
				"Packaging serverless functions for deployment...",
				"Component workflow packaged.",
			},
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			// Set up mocks for the current test case
			tc.setupMocks()
			

			progress := make(chan ProgressUpdate, 10) // Buffered channel
			var receivedUpdates []string
			done := make(chan struct{})
			ready := make(chan struct{})

			go func() {
				close(ready) // Signal that the goroutine is ready
				for update := range progress {
					receivedUpdates = append(receivedUpdates, update.Message)
				}
				close(done)
			}()

			<-ready // Wait for the goroutine to be ready

			err := PackageFuncs(progress)
			<-done // Wait for the goroutine to finish

			if (err != nil && tc.expectedErr == nil) || (err == nil && tc.expectedErr != nil) || (err != nil && tc.expectedErr != nil && err.Error() != tc.expectedErr.Error()) {
				t.Errorf("PackageFuncs() error = %v, expectedErr %v", err, tc.expectedErr)
			}

			if !slices.Equal(receivedUpdates, tc.expectedProgress) {
				t.Errorf("Expected progress updates %q, but got %q", tc.expectedProgress, receivedUpdates)
			}
		})
	}
}

func TestDeployWorkflow(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "test-deploy-")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(tmpDir)

	if err := os.WriteFile(filepath.Join(tmpDir, "switchboard.json"), []byte("{}"), 0644); err != nil {
		t.Fatal(err)
	}
	terraformDir := filepath.Join(tmpDir, "terraform")
	if err := os.Mkdir(terraformDir, 0755); err != nil {
		t.Fatal(err)
	}

	originalWd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	defer os.Chdir(originalWd)
	if err := os.Chdir(tmpDir); err != nil {
		t.Fatal(err)
	}


	originalExecCommand := execCommand
	defer func() { execCommand = originalExecCommand }()
	var capturedCmds [][]string
	execCommand = func(name string, arg ...string) *exec.Cmd {
		capturedCmds = append(capturedCmds, append([]string{name}, arg...))
		return exec.Command("true") // Simulate success
	}

	progress := make(chan ProgressUpdate, 10)
	if err := DeployWorkflow(progress); err != nil {
		t.Fatalf("DeployWorkflow() returned an error: %v", err)
	}

	expectedCmds := [][]string{
		{"terraform", "init"},
		{"terraform", "apply", "-auto-approve"},
	}

	if len(capturedCmds) != len(expectedCmds) {
		t.Fatalf("Expected %d commands, but got %d", len(expectedCmds), len(capturedCmds))
	}

	for i, expected := range expectedCmds {
		if !slices.Equal(capturedCmds[i], expected) {
			t.Errorf("Expected command %v, but got %v", expected, capturedCmds[i])
		}
	}

	expectedUpdates := []string{
		"Initializing and applying Terraform...",
		"Workflow deployed successfully.",
	}

	var receivedUpdates []string
	for update := range progress {
		receivedUpdates = append(receivedUpdates, update.Message)
	}

	if !slices.Equal(expectedUpdates, receivedUpdates) {
		t.Errorf("Expected progress updates %v, but got %v", expectedUpdates, receivedUpdates)
	}
}

func TestTeardownWorkflow(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "test-teardown-")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(tmpDir)

	if err := os.WriteFile(filepath.Join(tmpDir, "switchboard.json"), []byte("{}"), 0644); err != nil {
		t.Fatal(err)
	}
	terraformDir := filepath.Join(tmpDir, "terraform")
	if err := os.Mkdir(terraformDir, 0755); err != nil {
		t.Fatal(err)
	}

	originalWd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	defer os.Chdir(originalWd)
	if err := os.Chdir(tmpDir); err != nil {
		t.Fatal(err)
	}


	originalExecCommand := execCommand
	defer func() { execCommand = originalExecCommand }()

	var capturedCmds [][]string
	execCommand = func(name string, arg ...string) *exec.Cmd {
		capturedCmds = append(capturedCmds, append([]string{name}, arg...))
		return exec.Command("true") // Simulate success
	}

	progress := make(chan ProgressUpdate, 10)
	if err := TeardownWorkflow(progress); err != nil {
		t.Fatalf("TeardownWorkflow() returned an error: %v", err)
	}

	expectedCmds := [][]string{
		{"terraform", "destroy", "-auto-approve"},
	}

	if len(capturedCmds) != len(expectedCmds) {
		t.Fatalf("Expected %d commands, but got %d", len(expectedCmds), len(capturedCmds))
	}

	for i, expected := range expectedCmds {
		if !slices.Equal(capturedCmds[i], expected) {
			t.Errorf("Expected command %v, but got %v", expected, capturedCmds[i])
		}
	}

	expectedUpdates := []string{
		"Tearing down workflow components...",
		"Workflow components purged from the cloud.",
	}

	var receivedUpdates []string
	for update := range progress {
		receivedUpdates = append(receivedUpdates, update.Message)
	}

	if !slices.Equal(expectedUpdates, receivedUpdates) {
		t.Errorf("Expected progress updates %v, but got %v", expectedUpdates, receivedUpdates)
	}
}