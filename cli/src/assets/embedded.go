package assets

import "embed"

// The comment below recursively embeds all files from all subdirectories of the templates folder

//go:embed templates/**/*
var Templates embed.FS
