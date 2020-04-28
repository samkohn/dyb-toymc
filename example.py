"""A script that uses the toymc package."""

import argparse

from toymc.single import Single
from toymc.correlated import Correlated
from toymc.muon import Muon
from toymc import ToyMC


def main(outfile, runtime, seed):
    """Run the ToyMC with the given configuration."""
    toymc = ToyMC(outfile, runtime, seed=seed)
    single = Single("Single event", 20, 1, 1)
    ibd_nGd = Correlated("IBD nGd", 1, 1, 0.07, 28000)
    ibd_nH = Correlated("IBD nH", 1, 1, 0.06, 150000)
    ibd_nH.delayed_energy_spectrum = lambda rng: rng.uniform(1.9, 2.3)
    ibd_nH.prompt_delayed_distance_mm = 100
    muon = Muon("Muon", 1, 200)
    toymc.add_event_type(single)
    toymc.add_event_type(ibd_nGd)
    toymc.add_event_type(ibd_nH)
    toymc.add_event_type(muon)
    toymc.run()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Daya Bay Toy MC by Sam Kohn")
    parser.add_argument("outfile")
    parser.add_argument("-t", "--runtime", type=int)
    parser.add_argument("-s", "--seed", default=None, type=int)
    args = parser.parse_args()
    main(args.outfile, args.runtime, args.seed)
