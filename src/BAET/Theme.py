from rich.theme import Theme

app_theme = Theme(
    {
        "app.version": "italic bright_cyan",
        "argparse.arg_default": "dim italic",
        "argparse.arg_default_parens": "dim",
        "argparse.arg_default_value": "not italic bold dim",
        "argparse.help_keyword": "bold blue",
        "argparse.debug_todo": "reverse bold indian_red",
    }
)