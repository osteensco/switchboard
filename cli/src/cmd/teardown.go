package cmd

import (
	"fmt"
	"github.com/osteensco/switchboard/cli/core"
	"github.com/spf13/cobra"
)

var Teardown = &cobra.Command{
	Use:   "teardown",
	Short: "Teardown a deployed workflow.",
	Long:  "Teardown a deployed switchboard workflow from the cloud using terraform and remove all packaged files.",
	Run: func(cmd *cobra.Command, args []string) {
		progress := make(chan core.ProgressUpdate)
		var teardownErr error

		go func() {
			teardownErr = core.TeardownWorkflow(progress)
		}()

		for update := range progress {
			fmt.Println(update.Message)
		}

		if teardownErr != nil {
			fmt.Printf("Error: %v\n", teardownErr)
		}
	},
}
