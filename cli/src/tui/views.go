package tui

import (
	lg "github.com/charmbracelet/lipgloss"
)

type ViewFunc func(model) string

func renderMainView(m model) string {
	header := lg.NewStyle().
		Align(lg.Center).
		Width(m.width).
		Foreground(lg.Color("250")).
		Render("Switchboard")

	const maxCols = 3

	gapSize := (m.width - (m.boxWidth * maxCols)) / 16

	var rows []string
	var currentRow []string
	for i, opt := range options {

		var style lg.Style
		if i == m.cursor {
			style = selectedStyle(m.boxWidth, m.boxHeight)
		} else {
			style = defaultStyle(m.boxWidth, m.boxHeight).
				BorderForeground(lg.Color(colors[i])).
				Foreground(lg.Color(colors[i]))
		}
		style = style.MarginLeft(gapSize).MarginRight(gapSize)

		box := style.Render(opt)
		currentRow = append(currentRow, box)

		if len(currentRow) == maxCols || i == len(options)-1 {
			row := lg.JoinHorizontal(lg.Top, currentRow...)
			centeredRow := lg.NewStyle().
				Width(m.width).
				Align(lg.Center).
				Render(row)
			rows = append(rows, centeredRow)
			currentRow = nil
		}
	}

	return header + "\n\n" + lg.JoinVertical(lg.Left, rows...)
}

func renderLogsView(m model) string {
	// TODO implement
	return "Logs view here"
}

func renderDBView(m model) string {
	// TODO implement
	return "DB view here"
}

func renderWorkflowsView(m model) string {
	// TODO implement
	return "Workflows view here"
}

func renderMonitorView(m model) string {
	// TODO implement
	return "Monitor view here"
}

func renderScaffolderView(m model) string {
	// TODO implement
	return "Scaffolder view here"
}

func renderDeployerView(m model) string {
	// TODO implement
	return "Deployer view here"
}
