package core

import (
	"archive/zip"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"slices"
	"testing"
)

func TestShouldSkip(t *testing.T) {
	testCases := []struct {
		name     string
		isDir    bool
		expected bool
	}{
		{"workflow", true, false},
		{".dist", true, true},
		{"venv", true, true},
		{"__pycache__", true, true},
		{"node_modules", true, true},
		{".pytest_cache", true, true},
		{"main.py", false, false},
		{"workflow_lambda.zip", false, true},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			actual := shouldSkip(tc.name, tc.isDir)
			if actual != tc.expected {
				t.Errorf("shouldSkip(%q, %v) = %v; want %v", tc.name, tc.isDir, actual, tc.expected)
			}
		})
	}
}

func TestFindProjectRoot(t *testing.T) {
	// Setup a temporary directory structure
	rootDir, err := os.MkdirTemp("", "test-root-")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(rootDir)

	subDir := filepath.Join(rootDir, "subdir1", "subdir2")
	if err := os.MkdirAll(subDir, 0755); err != nil {
		t.Fatal(err)
	}

	// Create a dummy switchboard.json in the root
	configPath := filepath.Join(rootDir, "switchboard.json")
	if err := os.WriteFile(configPath, []byte("{}"), 0644); err != nil {
		t.Fatal(err)
	}

	// Test 1: Should find the root from a subdirectory
	t.Run("Finds Root from Subdirectory", func(t *testing.T) {
		// Change into the subdirectory
		originalDir, err := os.Getwd()
		if err != nil {
			t.Fatal(err)
		}
		defer os.Chdir(originalDir)
		if err := os.Chdir(subDir); err != nil {
			t.Fatal(err)
		}

		foundRoot, err := findProjectRoot()
		if err != nil {
			t.Fatalf("findProjectRoot() returned an error: %v", err)
		}

		if foundRoot != rootDir {
			t.Errorf("Expected to find root at %q, but found %q", rootDir, foundRoot)
		}
	})

	// Test 2: Should return an error if no config file is found
	t.Run("Fails when no config exists", func(t *testing.T) {
		// Change to a directory with no config file in its hierarchy
		emptyDir, err := os.MkdirTemp("", "empty-")
		if err != nil {
			t.Fatal(err)
		}
		defer os.RemoveAll(emptyDir)

		originalDir, err := os.Getwd()
		if err != nil {
			t.Fatal(err)
		}
		defer os.Chdir(originalDir)
		if err := os.Chdir(emptyDir); err != nil {
			t.Fatal(err)
		}

		_, err = findProjectRoot()
		if err == nil {
			t.Error("findProjectRoot() should have returned an error, but it didn't")
		}
	})
}

func TestPackageComponent(t *testing.T) {
	testCases := []struct {
		name             string
		language         string
		filesToCreate    map[string]string
		expectErr        bool
		expectedProgress []string
	}{
		{
			name:     "Python Success",
			language: "py",
			filesToCreate: map[string]string{
				"main.py":          "print('hello')",
				"requirements.txt": "boto3",
			},
			expectErr: false,
			expectedProgress: []string{
				"Packaging workflow...",
				"Installing Python dependencies from requirements.txt...",
				"workflow packaged successfully: " + filepath.Join("workflow", "workflow_lambda.zip"),
			},
		},
		{
			name:     "Node Success",
			language: "ts",
			filesToCreate: map[string]string{
				"index.ts":     "console.log('hello')",
				"package.json": `{"name": "test"}`,
			},
			expectErr: false,
			expectedProgress: []string{
				"Packaging workflow...",
				"Installing Node.js dependencies from package.json...",
				"workflow packaged successfully: " + filepath.Join("workflow", "workflow_lambda.zip"),
			},
		},
		{
			name:          "Component Dir Missing",
			language:      "py",
			filesToCreate: nil, // No component dir
			expectErr:     true,
			expectedProgress: []string{
				"Packaging workflow...",
			},
		},
		{
			name:     "Unsupported Language",
			language: "java",
			filesToCreate: map[string]string{
				"main.java": "public class Main {}",
			},
			expectErr: true,
			expectedProgress: []string{
				"Packaging workflow...",
			},
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			// Setup a temporary directory for each test run
			tmpDir, err := os.MkdirTemp("", "test-package-")
			if err != nil {
				t.Fatal(err)
			}
			defer os.RemoveAll(tmpDir)

			componentName := "workflow"
			componentPath := filepath.Join(tmpDir, componentName)

			if tc.filesToCreate != nil {
				if err := os.Mkdir(componentPath, 0755); err != nil {
					t.Fatal(err)
				}
				for name, content := range tc.filesToCreate {
					if err := os.WriteFile(filepath.Join(componentPath, name), []byte(content), 0644); err != nil {
						t.Fatal(err)
					}
				}
			}

			originalExecCommand := execCommand
			defer func() { execCommand = originalExecCommand }()
			execCommand = func(name string, arg ...string) *exec.Cmd {
				return exec.Command("true") // Simulate success
			}

			config := &ProjectConfig{Language: tc.language}
			progress := make(chan ProgressUpdate, 10) // Buffered channel for progress updates
			var receivedUpdates []string
			done := make(chan struct{})
			go func() {
				for update := range progress {
					receivedUpdates = append(receivedUpdates, update.Message)
				}
				close(done)
			}()

			err = packageComponent(componentName, config, tmpDir, progress)

			if (err != nil) != tc.expectErr {
				t.Errorf("packageComponent() error = %v, expectErr %v", err, tc.expectErr)
				return
			}

			if !tc.expectErr {
				zipFilePath := filepath.Join(componentPath, "workflow_lambda.zip")
				if _, err := os.Stat(zipFilePath); os.IsNotExist(err) {
					t.Errorf("Expected zip file to be created at: %s", zipFilePath)
				}

				if tc.language == "py" {
					// Unzip the file and verify its contents
					unzipDir := filepath.Join(componentPath, "unzipped")
					if err := unzip(zipFilePath, unzipDir); err != nil {
						t.Fatalf("Failed to unzip archive: %v", err)
					}

					expectedFilePath := filepath.Join(unzipDir, "main.py")
					if _, err := os.Stat(expectedFilePath); os.IsNotExist(err) {
						t.Errorf("Expected file to exist in archive: %s", expectedFilePath)
					}
				}
			}
		})
	}
}

func unzip(src, dest string) error {
	r, err := zip.OpenReader(src)
	if err != nil {
		return err
	}
	defer r.Close()

	for _, f := range r.File {
		fpath := filepath.Join(dest, f.Name)
		if f.FileInfo().IsDir() {
			os.MkdirAll(fpath, os.ModePerm)
			continue
		}

		if err := os.MkdirAll(filepath.Dir(fpath), os.ModePerm); err != nil {
			return err
		}

		out, err := os.OpenFile(fpath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, f.Mode())
		if err != nil {
			return err
		}

		rc, err := f.Open()
		if err != nil {
			return err
		}

		_, err = io.Copy(out, rc)

		out.Close()
		rc.Close()

		if err != nil {
			return err
		}
	}
	return nil
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
	if err := os.Chdir(tmpDir); err != nil {
		t.Fatal(err)
	}
	defer os.Chdir(originalWd)

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
	if err := os.Chdir(tmpDir); err != nil {
		t.Fatal(err)
	}
	defer os.Chdir(originalWd)

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

func TestInstallPipDependencies(t *testing.T) {
	// Create a temporary directory for the test
	tmpDir, err := os.MkdirTemp("", "test-pip-")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(tmpDir)

	// Create a dummy requirements.txt
	componentDir := filepath.Join(tmpDir, "workflow")
	if err := os.Mkdir(componentDir, 0755); err != nil {
		t.Fatal(err)
	}
	requirementsPath := filepath.Join(componentDir, "requirements.txt")
	if err := os.WriteFile(requirementsPath, []byte("boto3"), 0644); err != nil {
		t.Fatal(err)
	}

	// Mock exec.Command
	var capturedArgs []string
	originalExecCommand := execCommand
	execCommand = func(name string, arg ...string) *exec.Cmd {
		capturedArgs = append([]string{name}, arg...)
		// Return a dummy command that does nothing and succeeds
		return exec.Command("true")
	}
	defer func() { execCommand = originalExecCommand }()

	progress := make(chan ProgressUpdate)
	go func() {
		for range progress { // Drain channel
		}
	}()

	buildDir := filepath.Join(componentDir, ".dist")
	if err := installPipDependencies(componentDir, buildDir, progress); err != nil {
		t.Fatalf("installPipDependencies() returned an error: %v", err)
	}

	// Verify the command and arguments
	expectedArgs := []string{"pip", "install", "-r", requirementsPath, "-t", buildDir}
	if !slices.Equal(capturedArgs, expectedArgs) {
		t.Errorf("Expected command arguments %v, but got %v", expectedArgs, capturedArgs)
	}
}
