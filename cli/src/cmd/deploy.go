package cmd

import (
	"github.com/osteensco/switchboard/cli/core"
	"github.com/spf13/cobra"
)

var Deploy = &cobra.Command{
	Use:   "deploy",
	Short: "Deploy workflow.",
	Long:  "Deploy switchboard workflow to the cloud using terraform.",
	Run: func(cmd *cobra.Command, args []string) {
		core.DeployWorkflow()
	},
}
