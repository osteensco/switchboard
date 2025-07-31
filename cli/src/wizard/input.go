package wizard

import (
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
)

type inputModel struct {
	input  textinput.Model
	done   bool
	result string
	err    error
}

func initialInputModel(prompt string, placeholder string) inputModel {
	input := textinput.New()
	input.Placeholder = placeholder + "\n"
	input.Focus()
	input.Prompt = prompt + "\n"
	input.CharLimit = 256
	input.Width = 40

	return inputModel{input: input}
}

func (m inputModel) Init() tea.Cmd {
	return textinput.Blink
}

func (m inputModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.Type {
		case tea.KeyEnter:
			m.result = m.input.Value()
			m.done = true
			return m, tea.Quit
		case tea.KeyCtrlC:
			m.err = tea.ErrProgramKilled
			return m, tea.Quit
		}
	}

	var cmd tea.Cmd
	m.input, cmd = m.input.Update(msg)
	return m, cmd
}

func (m inputModel) View() string {
	if m.done {
		return ""
	}
	return m.input.View()
}

func Input(prompt string, placeholder string) (string, error) {
	p := tea.NewProgram(initialInputModel(prompt, placeholder))
	finalModel, err := p.Run()
	if err != nil {
		return "", err
	}
	return finalModel.(inputModel).result, finalModel.(inputModel).err
}
