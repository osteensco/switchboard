package core

import (
	"fmt"
)

func QueryLogs(workflow string, query string) string {
	fmt.Println("Querying logs....")
	fmt.Println("Workflow: " + workflow)
	fmt.Println("Query: " + query)

	return "results here"
}
