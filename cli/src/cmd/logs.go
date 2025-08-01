package cmd

import (
	"fmt"
	"os"

	"github.com/osteensco/switchboard/cli/core"
	"github.com/osteensco/switchboard/cli/wizard"
	"github.com/spf13/cobra"
)

var Logs = &cobra.Command{
	Use:   "logs",
	Short: "Retrieve logs for a given workflow.",
	Long:  "Query the logs for a workflow. If an empty query string is given, last 100 log entries are returned.",
	Run: func(cmd *cobra.Command, args []string) {
		var err error

		if workflow_name == "" {
			var inputPrompt = "Provide the name of your workflow."
			workflow_name, err = wizard.Input(inputPrompt, "myworkflow")
			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}
		}

		if logQuery == "" {
			// TODO add default query for last 100 entries.
		}
		core.QueryLogs(workflow_name, logQuery)
	},
}
