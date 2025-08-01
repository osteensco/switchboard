package cmd

import (
	"fmt"
	"os"

	"github.com/osteensco/switchboard/cli/core"
	"github.com/osteensco/switchboard/cli/wizard"
	"github.com/spf13/cobra"
)

var New = &cobra.Command{
	Use:   "new",
	Short: "Create new project scaffolding.",
	Long:  "Generate the core components of a Switchboard project including necessary Terraform and source code files",
	Run: func(cmd *cobra.Command, args []string) {
		var err error

		if workflow_name == "" {
			var inputPrompt = "Provide a name for your workflow."
			workflow_name, err = wizard.Input(inputPrompt, "myworkflow")
			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}
		}

		if cloud == "" {
			var cloudOptions = []string{"aws", "azure", "gcp"}
			var cloudTitle = "Choose a cloud provider"

			cloud, err = wizard.Select(cloudOptions, cloudTitle)
			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}
		}
		if lang == "" {
			var langOptions = []string{"py", "ts", "go"}
			var langTitle = "Choose a project language"

			lang, err = wizard.Select(langOptions, langTitle)
			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}
		}

		core.InitProject(workflow_name, cloud, lang)
	},
}
