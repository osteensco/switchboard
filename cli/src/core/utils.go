package core

import (
	"archive/zip"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"slices"
	"strings"

	"github.com/osteensco/switchboard/cli/assets"
)

func findProjectRoot() (string, error) {
	currentDir, err := os.Getwd()
	if err != nil {
		return "", err
	}

	for {
		configPath := filepath.Join(currentDir, "switchboard.json")
		if _, err := os.Stat(configPath); err == nil {
			return currentDir, nil
		}

		parentDir := filepath.Dir(currentDir)
		if parentDir == currentDir {
			return "", fmt.Errorf("switchboard.json not found in any parent directories")
		}
		currentDir = parentDir
	}
}

var loadConfig = func() (*ProjectConfig, string, error) {
	projectRoot, err := findProjectRoot()
	if err != nil {
		return nil, "", err
	}

	configPath := filepath.Join(projectRoot, "switchboard.json")
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, "", fmt.Errorf("could not read switchboard.json: %w", err)
	}

	var config ProjectConfig
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, "", fmt.Errorf("could not parse switchboard.json: %w", err)
	}

	return &config, projectRoot, nil
}

var getArn = func(progress chan<- ProgressUpdate) (string, error) {

	cmd := execCommand("aws", "iam", "get-role", "--role-name", "switchboard-role", "--query", "Role.Arn", "--output", "text")
	cmd.Stderr = os.Stderr

	arn_bytes, err := cmd.Output()
	if err != nil {
		progress <- ProgressUpdate{Message: fmt.Sprintf("Error querying for switchboard-role arn: %v", err)}
		return "", err
	}

	arn := strings.TrimSpace(string(arn_bytes))

	progress <- ProgressUpdate{Message: fmt.Sprintf("Retrieved arn: '%s'", arn)}

	return arn, nil
}

var packageComponent = func(componentName string, config *ProjectConfig, projectRoot string, progress chan<- ProgressUpdate) error {
	componentPath := filepath.Join(projectRoot, componentName)
	progress <- ProgressUpdate{Message: fmt.Sprintf("Packaging %s...", componentName)}

	if _, err := os.Stat(componentPath); os.IsNotExist(err) {
		return fmt.Errorf("%s directory not found", componentName)
	}

	buildDir := filepath.Join(componentPath, ".dist")
	if err := os.MkdirAll(buildDir, 0755); err != nil {
		return fmt.Errorf("failed to create build directory: %w", err)
	}
	// we keep the build dir so the user can debug easier if needed
	// defer os.RemoveAll(buildDir)

	if err := copySource(componentPath, buildDir); err != nil {
		return fmt.Errorf("failed to copy source code: %w", err)
	}

	if err := installDependencies(componentPath, buildDir, config.Language, progress); err != nil {
		return fmt.Errorf("failed to install dependencies: %w", err)
	}

	zipFileName := fmt.Sprintf("%s_lambda.zip", componentName)
	zipFilePath := filepath.Join(componentPath, zipFileName)
	if err := zipDirectory(buildDir, zipFilePath); err != nil {
		return fmt.Errorf("failed to create zip file: %w", err)
	}

	progress <- ProgressUpdate{Message: fmt.Sprintf("%s packaged successfully: %s", componentName, zipFilePath)}
	return nil
}

func installDependencies(componentDir, buildDir, language string, progress chan<- ProgressUpdate) error {
	switch language {
	case "py":
		return installPipDependencies(componentDir, buildDir, progress)
	case "ts":
		return installNpmDependencies(componentDir, buildDir, progress)
	case "go":
		return installGoDependencies(componentDir, buildDir, progress)
	default:
		return fmt.Errorf("unsupported language: %s", language)
	}
}

// Adding an alias for this function is useful for mocking in tests
var execCommand = exec.Command

func installPipDependencies(componentDir, buildDir string, progress chan<- ProgressUpdate) error {
	progress <- ProgressUpdate{Message: "Installing Python dependencies from requirements.txt..."}
	requirementsPath := filepath.Join(componentDir, "requirements.txt")
	if _, err := os.Stat(requirementsPath); os.IsNotExist(err) {
		progress <- ProgressUpdate{Message: "No requirements.txt found."}
		return err
	}
	cmd := execCommand("pip", "install", "-r", requirementsPath, "-t", buildDir)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		progress <- ProgressUpdate{Message: fmt.Sprintf("Error: pip install failed: %v", err)}
		return fmt.Errorf("pip install failed: %w", err)
	}
	return nil
}

func installNpmDependencies(componentDir, buildDir string, progress chan<- ProgressUpdate) error {
	progress <- ProgressUpdate{Message: "Installing Node.js dependencies from package.json..."}
	packageJsonPath := filepath.Join(componentDir, "package.json")
	if _, err := os.Stat(packageJsonPath); os.IsNotExist(err) {
		progress <- ProgressUpdate{Message: "No package.json found."}
		return err
	}

	cmd := execCommand("npm", "install", "--prefix", buildDir)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		progress <- ProgressUpdate{Message: fmt.Sprintf("Error: npm install failed: %v", err)}
		return fmt.Errorf("npm install failed: %w", err)
	}
	return nil
}

func installGoDependencies(componentDir, buildDir string, progress chan<- ProgressUpdate) error {
	progress <- ProgressUpdate{Message: "Tidying and building Go dependencies..."}
	goModPath := filepath.Join(componentDir, "go.mod")
	if _, err := os.Stat(goModPath); os.IsNotExist(err) {
		progress <- ProgressUpdate{Message: "No go.mod found."}
		return err
	}

	cmd := execCommand("go", "mod", "tidy")
	cmd.Dir = componentDir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		progress <- ProgressUpdate{Message: fmt.Sprintf("Error: go mod tidy failed: %v", err)}
		return fmt.Errorf("go mod tidy failed: %w", err)
	}

	cmd = execCommand("go", "build", "-o", buildDir)
	cmd.Dir = componentDir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		progress <- ProgressUpdate{Message: fmt.Sprintf("Error: go build failed: %v", err)}
		return fmt.Errorf("go build failed: %w", err)
	}

	return nil
}

func copySource(srcDir, destDir string) error {
	return filepath.Walk(srcDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if shouldSkip(info.Name(), info.IsDir()) {
			if info.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}

		destPath := filepath.Join(destDir, strings.TrimPrefix(path, srcDir))
		if info.IsDir() {
			return os.MkdirAll(destPath, info.Mode())
		}
		sourceFile, err := os.Open(path)
		if err != nil {
			return err
		}
		defer sourceFile.Close()

		destFile, err := os.Create(destPath)
		if err != nil {
			return err
		}
		defer destFile.Close()

		_, err = io.Copy(destFile, sourceFile)
		return err
	})
}

func shouldSkip(name string, isDir bool) bool {
	skipList := []string{".dist", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache"}

	if isDir {
		if slices.Contains(skipList, name) {
			return true
		}
	}

	if strings.HasSuffix(name, "_lambda.zip") {
		return true
	}

	return false
}

func zipDirectory(source, target string) error {
	zipfile, err := os.Create(target)
	if err != nil {
		return err
	}
	defer zipfile.Close()

	archive := zip.NewWriter(zipfile)
	defer archive.Close()

	filepath.Walk(source, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		header, err := zip.FileInfoHeader(info)
		if err != nil {
			return err
		}

		header.Name = strings.TrimPrefix(path, source+string(os.PathSeparator))
		if info.IsDir() {
			header.Name += "/"
		} else {
			header.Method = zip.Deflate
		}

		writer, err := archive.CreateHeader(header)
		if err != nil {
			return err
		}

		if !info.IsDir() {
			file, err := os.Open(path)
			if err != nil {
				return err
			}
			defer file.Close()
			_, err = io.Copy(writer, file)
		}
		return err
	})

	return nil
}

// copyFiles copies a specific list of files from a source directory in the embedded FS
// to a destination directory on the local filesystem. It skips files that don't exist in the source.
func copyFiles(srcDir, destDir string) error {
	files, err := assets.Templates.ReadDir(srcDir)
	if err != nil {
		return fmt.Errorf("failed to read embedded dir %s: %w", srcDir, err)
	}

	for _, file := range files {
		// we aren't copying subdirs
		if file.IsDir() {
			continue
		}

		srcPath := filepath.Join(srcDir, file.Name())
		destPath := filepath.Join(destDir, file.Name())

		content, err := assets.Templates.ReadFile(srcPath)
		if err != nil {
			return fmt.Errorf("failed to read embedded file %s: %w", srcPath, err)
		}

		if err := os.WriteFile(destPath, content, 0644); err != nil {
			return fmt.Errorf("failed to write file %s: %w", destPath, err)
		}
	}

	return nil
}

// copyDirectory recursively copies a directory from the embedded FS to the local filesystem.
func copyDirectory(srcDir, destDir string) error {
	return fs.WalkDir(assets.Templates, srcDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		relPath, err := filepath.Rel(srcDir, path)
		if err != nil {
			return err
		}
		destPath := filepath.Join(destDir, relPath)

		if relPath == "." {
			return nil
		}

		if d.IsDir() {
			return os.MkdirAll(destPath, 0755)
		}

		content, err := assets.Templates.ReadFile(path)
		if err != nil {
			return err
		}
		return os.WriteFile(destPath, content, 0644)
	})
}
