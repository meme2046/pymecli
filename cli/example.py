import typer

app = typer.Typer()


@app.command()
def hello(
    name: str = typer.Argument(
        help="Person to say hello to",
    ),
    from_name: str = typer.Option(
        "Pymecli",
        "-f",
        "--from",
        help="Who is saying hello",
    ),
):
    if from_name != "":
        print(f"Hello {name} from {from_name}!")
    else:
        print(f"Hello {name}!")


@app.command()
def goodbye(
    name: str = typer.Argument(
        help="Name of the person to goodbye",
    ),
    formal: bool = typer.Option(
        False,
        "--formal",
        "-f",
        help="是否为正式场合回答",
    ),
):
    if formal:
        print(f"Goodbye Ms. {name}. Have a good day.")
    else:
        print(f"Bye {name}!")
