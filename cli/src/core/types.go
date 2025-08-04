package core

// ProgressUpdate is used to send status messages from long-running core functions back to the calling UI (cmd or tui)
type ProgressUpdate struct {
	Message string
}
