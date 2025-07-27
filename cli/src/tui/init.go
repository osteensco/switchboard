package tui

import (
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"
	lg "github.com/charmbracelet/lipgloss"
)

var (
	colors = []string{"99", "111", "208", "105", "51", "202"}

	options = []string{"Logs", "DB", "Workflows", "Monitor", "Scaffolder", "Deployer"}

	views = []ViewFunc{renderLogsView, renderDBView, renderWorkflowsView, renderMonitorView, renderScaffolderView, renderDeployerView}

	optlen = len(options)
)

func selectedStyle(boxWidth int, boxHeight int) lg.Style {
	return lg.NewStyle().
		Align(lg.Center).
		Border(lg.RoundedBorder()).
		BorderForeground(lg.Color("212")).
		Foreground(lg.Color("229")).
		Background(lg.Color("57")).
		Padding(1, 2).
		Width(boxWidth).
		Height(boxHeight)
}

func defaultStyle(boxWidth int, boxHeight int) lg.Style {
	return lg.NewStyle().
		Align(lg.Center).
		Border(lg.RoundedBorder()).
		Padding(1, 2).
		Width(boxWidth).
		Height(boxHeight)
}

type model struct {
	width       int
	height      int
	boxWidth    int
	boxHeight   int
	currentView string
	cursor      int
	ready       bool
}

func initialModel() model {
	return model{currentView: "main"}
}

func (m model) Init() tea.Cmd {
	// Just return `nil`, which means "no I/O right now, please."
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		m.boxWidth = m.width / 9
		m.boxHeight = m.height / 12
		m.ready = true
	// handle key press
	case tea.KeyMsg:
		switch msg.String() {
		// exit the program.
		case "ctrl+c", "q":
			return m, tea.Quit

		// Movements
		//	m.cursor represents what index the cursor is on in the options slice

		// move the cursor up
		case "up", "k":
			if m.cursor > 2 { // max 3 per row
				m.cursor -= 3 // move up
			} else {
				m.cursor += 3 // cycle back down
			}
		// move the cursor down
		case "down", "j":
			if m.cursor <= 2 {
				m.cursor += 3
			} else {
				m.cursor -= 3
			}
		// move the cursor left
		case "left", "h":
			if m.cursor%3 != 0 {
				m.cursor--
			} else {
				m.cursor += 2
			}
		// move the cursor right
		case "right", "l":
			if (m.cursor+1)%3 != 0 {
				m.cursor++
			} else {
				m.cursor -= 2
			}

		// The "enter" key and the spacebar (a literal space) toggle
		// the selected state for the item that the cursor is pointing at.
		case "enter", " ":
			// TODO this should bring up another interface
			switch m.currentView {
			// TODO create enums for these
			case "main":
				m.currentView = options[m.cursor]
			}

			fmt.Printf("selected: %s\n", options[m.cursor])

		case "esc", "backspace":
			switch m.currentView {
			case "main":
			default:
				m.currentView = "main"
			}
		}
	}
	// Return the updated model to the Bubble Tea runtime for processing.
	// Note that we're not returning a command.
	return m, nil
}

// The view is just one big string that gets passed to the UI for rendering
func (m model) View() string {
	if !m.ready {
		return "Loading..."
	}
	switch m.currentView {
	case "main":
		return renderMainView(m)
	default:
		return views[m.cursor](m)
	}
}

func Run() {
	p := tea.NewProgram(initialModel(), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Printf("TUI Error: %v/n", err)
		os.Exit(1)
	}
}
