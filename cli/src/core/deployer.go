package core

import (
	"archive/zip"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"slices"
	"strings"
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

func loadConfig() (*ProjectConfig, string, error) {
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

func PackageFuncs(progress chan<- ProgressUpdate) error {
	defer close(progress)

	config, projectRoot, err := loadConfig()
	if err != nil {
		return err
	}

	progress <- ProgressUpdate{Message: "Packaging serverless functions for deployment..."}

	if err := packageComponent("workflow", config, projectRoot, progress); err != nil {
		return fmt.Errorf("error packaging workflow: %w", err)
	}

	if err := packageComponent("executor", config, projectRoot, progress); err != nil {
		return fmt.Errorf("error packaging executor: %w", err)
	}

	progress <- ProgressUpdate{Message: "Packaging complete."}
	return nil
}

func packageComponent(componentName string, config *ProjectConfig, projectRoot string, progress chan<- ProgressUpdate) error {
	componentPath := filepath.Join(projectRoot, componentName)
	progress <- ProgressUpdate{Message: fmt.Sprintf("Packaging %s...", componentName)}

	if _, err := os.Stat(componentPath); os.IsNotExist(err) {
		return fmt.Errorf("%s directory not found", componentName)
	}

	buildDir := filepath.Join(componentPath, ".dist")
	if err := os.MkdirAll(buildDir, 0755); err != nil {
		return fmt.Errorf("failed to create build directory: %w", err)
	}
	defer os.RemoveAll(buildDir)

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

var execCommand = exec.Command

func installPipDependencies(componentDir, buildDir string, progress chan<- ProgressUpdate) error {
	progress <- ProgressUpdate{Message: "Installing Python dependencies from requirements.txt..."}
	requirementsPath := filepath.Join(componentDir, "requirements.txt")
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
		progress <- ProgressUpdate{Message: "No package.json found, skipping npm install."}
		return nil
	}

	cmd := execCommand("npm", "install", "--prefix", componentDir)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("npm install failed: %w", err)
	}
	return nil
}

func installGoDependencies(componentDir, buildDir string, progress chan<- ProgressUpdate) error {
	progress <- ProgressUpdate{Message: "Tidying and building Go dependencies..."}
	goModPath := filepath.Join(componentDir, "go.mod")
	if _, err := os.Stat(goModPath); os.IsNotExist(err) {
		progress <- ProgressUpdate{Message: "No go.mod found, skipping go build."}
		return nil
	}

	cmd := execCommand("go", "mod", "tidy")
	cmd.Dir = componentDir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("go mod tidy failed: %w", err)
	}

	cmd = execCommand("go", "build", "-o", buildDir)
	cmd.Dir = componentDir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
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

func DeployWorkflow(progress chan<- ProgressUpdate) error {
	defer close(progress)

	progress <- ProgressUpdate{Message: "Initializing and applying Terraform..."}

	projectRoot, err := findProjectRoot()
	if err != nil {
		return err
	}

	terraformDir := filepath.Join(projectRoot, "terraform")

	initCmd := execCommand("terraform", "init")
	initCmd.Dir = terraformDir
	initCmd.Stdout = os.Stdout
	initCmd.Stderr = os.Stderr
	if err := initCmd.Run(); err != nil {
		progress <- ProgressUpdate{Message: fmt.Sprintf("Error running terraform init: %v", err)}
		return fmt.Errorf("error running terraform init: %w", err)
	}

	applyCmd := execCommand("terraform", "apply", "-auto-approve")
	applyCmd.Dir = terraformDir
	applyCmd.Stdout = os.Stdout
	applyCmd.Stderr = os.Stderr
	if err := applyCmd.Run(); err != nil {
		progress <- ProgressUpdate{Message: fmt.Sprintf("Error running terraform apply: %v", err)}
		return fmt.Errorf("error running terraform apply: %w", err)
	}

	progress <- ProgressUpdate{Message: "Workflow deployed successfully."}
	return nil
}

func TeardownWorkflow(progress chan<- ProgressUpdate) error {
	defer close(progress)

	progress <- ProgressUpdate{Message: "Tearing down workflow components..."}

	projectRoot, err := findProjectRoot()
	if err != nil {
		return err
	}

	terraformDir := filepath.Join(projectRoot, "terraform")

	destroyCmd := execCommand("terraform", "destroy", "-auto-approve")
	destroyCmd.Dir = terraformDir
	destroyCmd.Stdout = os.Stdout
	destroyCmd.Stderr = os.Stderr
	if err := destroyCmd.Run(); err != nil {
		progress <- ProgressUpdate{Message: fmt.Sprintf("Error running terraform destroy: %v", err)}
		return fmt.Errorf("error running terraform destroy: %w", err)
	}

	progress <- ProgressUpdate{Message: "Workflow components purged from the cloud."}
	return nil
}

