package core

import (
	"archive/zip"
	"fmt"
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
		expectedProgress func(string, string) []string
	}{
		{
			name:     "Python Success",
			language: "py",
			filesToCreate: map[string]string{
				"main.py":          "print('hello')",
				"requirements.txt": "boto3",
			},
			expectErr: false,
			expectedProgress: func(tmpDir string, componentName string) []string {
				return []string{
					"Packaging workflow...",
					"Installing Python dependencies from requirements.txt...",
					fmt.Sprintf("workflow packaged successfully: %s", filepath.Join(tmpDir, componentName, "workflow_lambda.zip")),
				}
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
			expectedProgress: func(tmpDir string, componentName string) []string {
				return []string{
					"Packaging workflow...",
					"Installing Node.js dependencies from package.json...",
					fmt.Sprintf("workflow packaged successfully: %s", filepath.Join(tmpDir, componentName, "workflow_lambda.zip")),
				}
			},
		},
		{
			name:          "Component Dir Missing",
			language:      "py",
			filesToCreate: nil, // No component dir
			expectErr:     true,
			expectedProgress: func(tmpDir string, componentName string) []string {
				return []string{
					"Packaging workflow...",
				}
			},
		},
		{
			name:     "Unsupported Language",
			language: "java",
			filesToCreate: map[string]string{
				"main.java": "public class Main {}",
			},
			expectErr: true,
			expectedProgress: func(tmpDir string, componentName string) []string {
				return []string{
					"Packaging workflow...",
				}
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
			close(progress)
			<-done

			if (err != nil) != tc.expectErr {
				t.Errorf("packageComponent() error = %v, expectErr %v", err, tc.expectErr)
				return
			}

			// Check that the progress updates match the expected updates.
			expected := tc.expectedProgress(tmpDir, componentName)
			if !slices.Equal(expected, receivedUpdates) {
				t.Errorf("Expected progress updates %q, but got %q", expected, receivedUpdates)
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

func TestInstallDependencies(t *testing.T) {
	type setupFunc func(tmpDir, componentDir string) error
	type expectedCmdsFunc func(componentDir, buildDir string) [][]string

	testCases := []struct {
		name             string
		language         string
		setup            setupFunc
		mockCmds         map[string]func(args []string) *exec.Cmd // Map command name to a function that returns a mocked Cmd
		expectedCmds     expectedCmdsFunc                         // Changed to a function
		expectedProgress []string
		expectErr        bool
	}{
		{
			name:     "Python Success",
			language: "py",
			setup: func(tmpDir, componentDir string) error {
				return os.WriteFile(filepath.Join(componentDir, "requirements.txt"), []byte("boto3"), 0644)
			},
			mockCmds: map[string]func(args []string) *exec.Cmd{
				"pip": func(args []string) *exec.Cmd {
					return exec.Command("true") // Simulate success
				},
			},
			expectedCmds: func(componentDir, buildDir string) [][]string {
				return [][]string{
					{"pip", "install", "-r", filepath.Join(componentDir, "requirements.txt"), "-t", buildDir},
				}
			},
			expectedProgress: []string{
				"Installing Python dependencies from requirements.txt...",
			},
			expectErr: false,
		},
		{
			name:     "Python Failure",
			language: "py",
			setup: func(tmpDir, componentDir string) error {
				return os.WriteFile(filepath.Join(componentDir, "requirements.txt"), []byte("boto3"), 0644)
			},
			mockCmds: map[string]func(args []string) *exec.Cmd{
				"pip": func(args []string) *exec.Cmd {
					return exec.Command("false") // Simulate failure
				},
			},
			expectedCmds: func(componentDir, buildDir string) [][]string {
				return [][]string{
					{"pip", "install", "-r", filepath.Join(componentDir, "requirements.txt"), "-t", buildDir},
				}
			},
			expectedProgress: []string{
				"Installing Python dependencies from requirements.txt...",
				"Error: pip install failed: exit status 1",
			},
			expectErr: true,
		},
		{
			name:     "Node.js Success",
			language: "ts",
			setup: func(tmpDir, componentDir string) error {
				return os.WriteFile(filepath.Join(componentDir, "package.json"), []byte(`{"name": "test"}`), 0644)
			},
			mockCmds: map[string]func(args []string) *exec.Cmd{
				"npm": func(args []string) *exec.Cmd {
					return exec.Command("true") // Simulate success
				},
			},
			expectedCmds: func(componentDir, buildDir string) [][]string {
				return [][]string{
					{"npm", "install", "--prefix", buildDir},
				}
			},
			expectedProgress: []string{
				"Installing Node.js dependencies from package.json...",
			},
			expectErr: false,
		},
		{
			name:     "Node.js Failure",
			language: "ts",
			setup: func(tmpDir, componentDir string) error {
				return os.WriteFile(filepath.Join(componentDir, "package.json"), []byte(`{"name": "test"}`), 0644)
			},
			mockCmds: map[string]func(args []string) *exec.Cmd{
				"npm": func(args []string) *exec.Cmd {
					return exec.Command("false") // Simulate failure
				},
			},
			expectedCmds: func(componentDir, buildDir string) [][]string {
				return [][]string{
					{"npm", "install", "--prefix", buildDir},
				}
			},
			expectedProgress: []string{
				"Installing Node.js dependencies from package.json...",
				"Error: npm install failed: exit status 1",
			},
			expectErr: true,
		},
		{
			name:     "Go Success",
			language: "go",
			setup: func(tmpDir, componentDir string) error {
				return os.WriteFile(filepath.Join(componentDir, "go.mod"), []byte("module test"), 0644)
			},
			mockCmds: map[string]func(args []string) *exec.Cmd{
				"go": func(args []string) *exec.Cmd {
					return exec.Command("true") // Simulate success for both tidy and build
				},
			},
			expectedCmds: func(componentDir, buildDir string) [][]string {
				return [][]string{
					{"go", "mod", "tidy"},
					{"go", "build", "-o", buildDir},
				}
			},
			expectedProgress: []string{
				"Tidying and building Go dependencies...",
			},
			expectErr: false,
		},
		{
			name:     "Go Tidy Failure",
			language: "go",
			setup: func(tmpDir, componentDir string) error {
				return os.WriteFile(filepath.Join(componentDir, "go.mod"), []byte("module test"), 0644)
			},
			mockCmds: map[string]func(args []string) *exec.Cmd{
				"go": func(args []string) *exec.Cmd {
					if slices.Contains(args, "tidy") {
						return exec.Command("false") // Simulate tidy failure
					}
					return exec.Command("true") // Build would not run
				},
			},
			expectedCmds: func(componentDir, buildDir string) [][]string {
				return [][]string{
					{"go", "mod", "tidy"},
				}
			},
			expectedProgress: []string{
				"Tidying and building Go dependencies...",
				"Error: go mod tidy failed: exit status 1",
			},
			expectErr: true,
		},
		{
			name:     "Go Build Failure",
			language: "go",
			setup: func(tmpDir, componentDir string) error {
				return os.WriteFile(filepath.Join(componentDir, "go.mod"), []byte("module test"), 0644)
			},
			mockCmds: map[string]func(args []string) *exec.Cmd{
				"go": func(args []string) *exec.Cmd {
					if slices.Contains(args, "build") {
						return exec.Command("false") // Simulate build failure
					}
					return exec.Command("true") // Tidy would succeed
				},
			},
			expectedCmds: func(componentDir, buildDir string) [][]string {
				return [][]string{
					{"go", "mod", "tidy"},
					{"go", "build", "-o", buildDir},
				}
			},
			expectedProgress: []string{
				"Tidying and building Go dependencies...",
				"Error: go build failed: exit status 1",
			},
			expectErr: true,
		},
		{
			name:     "Unsupported Language",
			language: "unsupported",
			setup: func(tmpDir, componentDir string) error {
				return nil
			},
			mockCmds:         nil,
			expectedCmds:     func(componentDir, buildDir string) [][]string { return [][]string{} },
			expectedProgress: []string{},
			expectErr:        true,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			// Setup temporary directories
			tmpDir, err := os.MkdirTemp("", "test-install-deps-")
			if err != nil {
				t.Fatal(err)
			}
			defer os.RemoveAll(tmpDir)

			componentDir := filepath.Join(tmpDir, "workflow")
			if err := os.Mkdir(componentDir, 0755); err != nil {
				t.Fatal(err)
			}
			buildDir := filepath.Join(componentDir, ".dist")
			if err := os.Mkdir(buildDir, 0755); err != nil {
				t.Fatal(err)
			}

			// Perform setup for the test case
			if tc.setup != nil {
				if err := tc.setup(tmpDir, componentDir); err != nil {
					t.Fatalf("setup failed: %v", err)
				}
			}

			// Mock exec.Command
			originalExecCommand := execCommand
			defer func() { execCommand = originalExecCommand }()

			var capturedCmds [][]string
			execCommand = func(name string, arg ...string) *exec.Cmd {
				capturedCmds = append(capturedCmds, append([]string{name}, arg...))
				mockFunc, ok := tc.mockCmds[name]
				if ok {
					return mockFunc(arg)
				}
				// Default to success if not explicitly mocked
				return exec.Command("true")
			}

			// Capture progress updates
			progress := make(chan ProgressUpdate, 10) // Buffered channel
			var receivedUpdates []string
			done := make(chan struct{})
			go func() {
				for update := range progress {
					receivedUpdates = append(receivedUpdates, update.Message)
				}
				close(done)
			}()

			// Call the function under test
			err = installDependencies(componentDir, buildDir, tc.language, progress)
			close(progress) // Close the channel to signal the goroutine to stop
			<-done          // Wait for the goroutine to finish

			// Assert error
			if (err != nil) != tc.expectErr {
				t.Errorf("installDependencies() error = %v, expectErr %v", err, tc.expectErr)
			}

			// Assert captured commands
			expectedCmds := tc.expectedCmds(componentDir, buildDir) // Generate expected commands dynamically
			if !slices.EqualFunc(capturedCmds, expectedCmds, func(a, b []string) bool {
				return slices.Equal(a, b)
			}) {
				t.Errorf("Expected commands %v, but got %v", expectedCmds, capturedCmds)
			}

			// Assert progress updates
			if !slices.Equal(receivedUpdates, tc.expectedProgress) {
				t.Errorf("Expected progress updates %v, but got %v", tc.expectedProgress, receivedUpdates)
			}
		})
	}
}
