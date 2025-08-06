package cmd

import (
	"fmt"
	"github.com/osteensco/switchboard/cli/core"
	"github.com/spf13/cobra"
)

var Deploy = &cobra.Command{
	Use:   "deploy",
	Short: "Deploy workflow.",
	Long:  "Deploy switchboard workflow to the cloud using terraform.",
	Run: func(cmd *cobra.Command, args []string) {
		progress := make(chan core.ProgressUpdate)
		var deployErr error

		go func() {
			deployErr = core.DeployWorkflow(progress)
		}()

		for update := range progress {
			fmt.Println(update.Message)
		}

		if deployErr != nil {
			fmt.Printf("Error: %v\n", deployErr)
		}
	},
}
