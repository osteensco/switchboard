package core

import (
	"fmt"
)

func PackageFuncs() {
	fmt.Println("Packaged serverless functions for deployment.")
}

func DeployWorkflow() {
	fmt.Println("Workflow deployed.")
}

func TeardownWorkflow() {
	fmt.Println("Workflow components purged from the cloud.")
}
