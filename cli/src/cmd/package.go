package cmd

import (
	"github.com/osteensco/switchboard/cli/core"
	"github.com/spf13/cobra"
)

var Package = &cobra.Command{
	Use:   "package",
	Short: "Package Switchboard components for deployment.",
	Long:  "Package the workflow and execution functions and ensure terraform is initialized and valid.",
	Run: func(cmd *cobra.Command, args []string) {
		core.PackageFuncs()
	},
}
