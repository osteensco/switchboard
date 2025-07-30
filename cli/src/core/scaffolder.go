package core

import (
	"fmt"
)

// TODO
// 	- init
// 		- brings up wizard (bubbletea, non tui) to select options
// 		- all options should correspond to flags and arguments

func InitProject(cloud string, lang string) {
	switch cloud {
	case "aws", "gcp", "azure":
		fmt.Printf("Init New Project in %s\n", cloud)
	default:
		fmt.Printf("'%s' is an invalid option, please use one of 'aws', 'gcp', or 'azure'\n", cloud)
	}
	switch lang {
	case "py", "ts", "go":
		fmt.Printf("Init New %s Project\n", lang)
	default:
		fmt.Printf("'%s' is an invalid option, please use one of 'py', 'ts', or 'go'\n", lang)
	}
}
