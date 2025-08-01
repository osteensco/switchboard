package cmd

import (
	"github.com/osteensco/switchboard/cli/core"
	"github.com/spf13/cobra"
)

var Teardown = &cobra.Command{
	Use:   "teardown",
	Short: "Teardown a deployed workflow.",
	Long:  "Teardown a deployed switchboard workflow from the cloud using terraform and remove all packaged files.",
	Run: func(cmd *cobra.Command, args []string) {
		core.TeardownWorkflow()
	},
}
