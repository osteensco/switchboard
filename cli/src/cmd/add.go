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
			var triggerOptions = []string{"endpoint", "cron", "listener", "subscriber", "custom"}
			var triggerTitle = "Choose a prefabricated trigger, or implement a custom one."
			// What additional information is needed for custom triggers?
			trigger, err = wizard.Select(triggerOptions, triggerTitle)
			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}
		}

		// Cloud and SDK need to be read from the project's switchboard.json file
		config, err := core.GetConfig()
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}

		core.AddTrigger(trigger, config["name"], config["lang"], config["cloud"])
	},
}
