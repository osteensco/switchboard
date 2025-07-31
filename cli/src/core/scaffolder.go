package core

import (
	"fmt"
)

func InitProject(cloud string, lang string) {
	// TODO
	// - handle project name
	// - generate project structure
	// - populate project with template files
	// - generate config file

	switch cloud {
	case "aws", "gcp", "azure":
		fmt.Printf("Init New Project in %s\n", cloud)
	default:
		fmt.Printf("'%s' is an invalid option, please use one of 'aws', 'gcp', or 'azure'\n", cloud)
		return
	}
	switch lang {
	case "py", "ts", "go":
		fmt.Printf("Init New %s Project\n", lang)
	default:
		fmt.Printf("'%s' is an invalid option, please use one of 'py', 'ts', or 'go'\n", lang)
		return
	}
}
