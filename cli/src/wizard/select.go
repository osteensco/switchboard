package wizard

import (
	"fmt"

	"github.com/charmbracelet/bubbles/list"
	tea "github.com/charmbracelet/bubbletea"
)

type item string

func (i item) Title() string       { return string(i) }
func (i item) Description() string { return "" }
func (i item) FilterValue() string { return string(i) }

type selectModel struct {
	width    int
	height   int
	list     list.Model
	selected string
	ready    bool
	done     bool
}

func initialSelectModel(opts []string, title string) selectModel {
	items := make([]list.Item, len(opts))
	for i, val := range opts {
		items[i] = item(val)
	}
	l := list.New(items, list.NewDefaultDelegate(), 0, 0)
	l.Title = title
	return selectModel{list: l}
}

func (m selectModel) Init() tea.Cmd {
	return nil
}

func (m selectModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width / 2
		m.height = msg.Height
		m.ready = true
		m.list.SetSize(m.width, m.height)
	case tea.KeyMsg:
		switch msg.String() {
		case "enter":
			i := m.list.SelectedItem().(item)
			m.selected = string(i)
			m.done = true
			return m, tea.Quit
		case "ctrl+c", "q":
			return m, tea.Quit
		}
	}

	var cmd tea.Cmd
	m.list, cmd = m.list.Update(msg)
	return m, cmd
}

func (m selectModel) View() string {
	if m.done {
		return fmt.Sprintf("Selected: %s\n", m.selected)
	}
	return m.list.View()
}

func Select(opts []string, title string) (string, error) {
	p := tea.NewProgram(initialSelectModel(opts, title), tea.WithAltScreen())
	finalModel, err := p.Run()
	if err != nil {
		return "", err
	}
	return finalModel.(selectModel).selected, nil
}
