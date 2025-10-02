package core

// ProgressUpdate is used to send status messages from long-running core functions back to the calling UI (cmd or tui)

type ProgressUpdate struct {
	Message string
}

type ProjectConfig struct {
	Name     string `json:"name"`
	Language string `json:"language"`
	Cloud    string `json:"cloud"`
	Trigger  string `json:"trigger"`
}

// Directories within a generated switchboard project
type projectPaths struct {
	Workflow  string
	Executor  string
	Terraform string
	Trigger   string
}

// Directories within the switchboard file template
type templatePaths struct {
	Root      string
	Language  string
	Terraform string
	Triggers  string
}
