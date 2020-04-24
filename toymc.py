"""Toy MC main module."""
import argparse


def main(outfile):
    with open(outfile, "w") as f_out:
        f_out.write("123")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Daya Bay Toy MC by Sam Kohn")
    parser.add_argument("outfile")
    args = parser.parse_args()
    main(args.outfile)
