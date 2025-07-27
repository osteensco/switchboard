package cmd

import (
	"fmt"
	"os"

	"github.com/osteensco/switchboard/cli/tui"
	"github.com/spf13/cobra"
)

var (
	// add other flags and stuff here

	rootCmd = &cobra.Command{
		Use:   "sb",
		Short: "The companion CLI tool for the Switchboard orchestration framework.",
		Long: `Switchboard is a serverless, event-driven, orchestration framework. 
This CLI tool allows you to create, deploy, and monitor your workflows made with Switchboard.
`,
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) == 0 {
				tui.Run()
				return
			}
			_ = cmd.Help()
		},
	}
)

func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

// each cmd.go file should have it's own init function instead of living here
func init() {
	// add config, commands, flags, defaults, etc here
	return
}
