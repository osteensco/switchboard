package core

import (
	"fmt"
)

func InitProject(name string, cloud string, lang string) {
	// TODO
	// - handle project name
	// - generate project structure
	// - populate project with template files
	// - generate config file
	fmt.Println("Workflow name: " + name)

	switch cloud {
	case "aws", "gcp", "azure":
		fmt.Printf("Cloud provider: %s\n", cloud)
	default:
		fmt.Printf("'%s' is an invalid option, please use one of 'aws', 'gcp', or 'azure'\n", cloud)
		return
	}
	switch lang {
	case "py", "ts", "go":
		fmt.Printf("SDK: %s \n", lang)
	default:
		fmt.Printf("'%s' is an invalid option, please use one of 'py', 'ts', or 'go'\n", lang)
		return
	}
}

func AddTrigger(trigger string) {
	fmt.Println("Trigger added: " + trigger)
}
