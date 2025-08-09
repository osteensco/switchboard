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
	RunE: func(cmd *cobra.Command, args []string) error {
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

		// Get cloud specific terraform information
		switch cloud {
		// TODO
		//	- Need a function to pass env variables to terraform like in the command below. This should provide a mechanism to pass secrets to terraform at runtime.
		//	- Note: This will need to handle each cloud providers nuances.
		// 		export TF_VAR_switchboard_role_arn=$(aws iam get-role --role-name switchboard-role --query 'Role.Arn' --output text)
		case "aws":
			var arn_prompt = "Please provide the switchboard-role arn."
			tf_vars["switchboard_role_arn"], err = wizard.Input(arn_prompt, "arn:aws:iam::<account_id>:role/switchboard-role")
			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}
		}

		progress := make(chan core.ProgressUpdate)
		var initErr error
		go func() {
			initErr = core.InitProject(workflow_name, cloud, lang, tf_vars, progress)
		}()

		for update := range progress {
			fmt.Println(update.Message)
		}

		return initErr
	},
}
