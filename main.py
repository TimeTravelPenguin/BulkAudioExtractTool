from rich import print as pprint

from BAET.AppArgs import GetArgs


def main():
    args = GetArgs()
    pprint(args)


if __name__ == "__main__":
    main()
