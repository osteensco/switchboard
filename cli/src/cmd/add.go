package cmd

import (
	"fmt"
	"os"

	"github.com/osteensco/switchboard/cli/core"
	"github.com/osteensco/switchboard/cli/wizard"
	"github.com/spf13/cobra"
)

var Add = &cobra.Command{
	Use:   "add",
	Short: "Add a trigger for the workflow",
	Long:  "Generate the required files for the chosen prefabricated trigger.",
	Run: func(cmd *cobra.Command, args []string) {
		var err error

		if trigger == "" {
			var triggerOptions = []string{"aws", "azure", "gcp"}
			var triggerTitle = "Choose a prefabricated trigger."

			trigger, err = wizard.Select(triggerOptions, triggerTitle)
			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}
		}

		core.AddTrigger(trigger)
	},
}
