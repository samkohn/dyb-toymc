"""Toy MC main module."""
import argparse
from collections import namedtuple
from operator import attrgetter
from abc import ABC, abstractmethod
from numpy.random import default_rng

import root_util as util


class ToyMC:
    """The Toy MC execution class."""

    def __init__(
        self,
        outfile,
        duration,
        reco_name="AdSimpleNL",
        calib_name="CalibStats",
        seed=None,
    ):
        from ROOT import TFile  # pylint: disable=no-name-in-module

        self.outfile = TFile(outfile, "RECREATE")
        self.event_types = []
        self.duration = duration
        self.rng = default_rng(seed)
        self.reco_name = reco_name
        self.calib_name = calib_name

    def add_event_type(self, event_type):
        """Add the specified event type to the ToyMC."""
        self.event_types.append(event_type)

    def run(self):
        """Run the ToyMC and save the output."""
        output = MCOutput(
            self.outfile, reco_name=self.reco_name, calib_name=self.calib_name
        )
        events = []
        for event_type in self.event_types:
            new_events = event_type.generate_events(self.rng, self.duration)
            events.extend(new_events)
        events.sort(key=attrgetter("timestamp"))
        for event in events:
            output.add(event)
        self.finalize()

    def finalize(self):
        """Safely save and close out all ToyMC resources."""
        self.outfile.Write()
        self.outfile.Close()


class MCOutput:
    """The ToyMC output data structure."""

    def __init__(self, container, reco_name, calib_name):
        from ROOT import TTree  # pylint: disable=no-name-in-module

        self.container = container
        self.container.cd()
        self.reco_ttree, self.reco_buf = self.prep_reco(
            TTree, self.container, reco_name
        )
        self.calib_ttree, self.calib_buf = self.prep_calib(
            TTree, self.container, calib_name
        )

    def add(self, event):
        """Add the given event to the output data structure."""
        rb = self.reco_buf
        cb = self.calib_buf
        util.assign_value(cb.triggerNumber, event.trigger_number)
        util.assign_value(cb.detector, event.detector)
        timestamp_seconds = event.timestamp // 1000000000
        timestamp_nanoseconds = event.timestamp % 1000000000
        util.assign_value(cb.timestamp_seconds, timestamp_seconds)
        util.assign_value(cb.timestamp_nanoseconds, timestamp_nanoseconds)
        util.assign_value(cb.nHit, event.nHit)
        util.assign_value(cb.charge, event.charge)
        util.assign_value(cb.fQuad, event.fQuad)
        util.assign_value(cb.fMax, event.fMax)
        util.assign_value(cb.fPSD_t1, event.fPSD_t1)
        util.assign_value(cb.fPSD_t2, event.fPSD_t2)
        util.assign_value(cb.f2inch_maxQ, event.f2inch_maxQ)

        util.assign_value(rb.triggerType, event.trigger_type)
        util.assign_value(rb.site, event.site)
        util.assign_value(rb.energy, event.energy)
        util.assign_value(rb.x, event.x)
        util.assign_value(rb.y, event.y)
        util.assign_value(rb.z, event.z)

        self.reco_ttree.Fill()
        self.calib_ttree.Fill()

    @staticmethod
    def prep_calib(TTree, host_file, name):
        """Create the "calib" (~CalibStats) TTree and fill buffer.

        Return a tuple of (calibStats, buffer) containing the TTree object and the
        buffer used to fill its TBranches.
        """
        buf = util.TreeBuffer()
        buf.triggerNumber = util.int_value()
        buf.detector = util.int_value()
        buf.timestamp_seconds = util.int_value()
        buf.timestamp_nanoseconds = util.int_value()
        buf.nHit = util.int_value()
        buf.charge = util.float_value()
        buf.fQuad = util.float_value()
        buf.fMax = util.float_value()
        buf.fPSD_t1 = util.float_value()
        buf.fPSD_t2 = util.float_value()
        buf.f2inch_maxQ = util.float_value()

        host_file.cd()
        event_subdir = host_file.Get("Event")
        if not bool(event_subdir):
            event_subdir = host_file.mkdir("Event")
        event_subdir.cd()
        data_subdir = event_subdir.Get("Data")
        if not bool(data_subdir):
            data_subdir = event_subdir.mkdir("Data")
        data_subdir.cd()
        long_name = "Tree at /Event/Data/{name} holding Data_{name}".format(name=name)
        calib = TTree(name, long_name)
        calib.Branch("triggerNumber", buf.triggerNumber, "triggerNumber/I")
        calib.Branch(
            "context.mTimeStamp.mSec",
            buf.timestamp_seconds,
            "context.mTimeStamp.mSec/I",
        )
        calib.Branch(
            "context.mTimeStamp.mNanoSec",
            buf.timestamp_nanoseconds,
            "context.mTimeStamp.mNanoSec/I",
        )
        calib.Branch("context.mDetId", buf.detector, "context.mDetId/I")
        calib.Branch("nHit", buf.nHit, "nHit/I")
        calib.Branch("NominalCharge", buf.charge, "NominalCharge/F")
        calib.Branch("Quadrant", buf.fQuad, "Quadrant/F")
        calib.Branch("MaxQ", buf.fMax, "MaxQ/F")
        calib.Branch("time_PSD", buf.fPSD_t1, "time_PSD/F")
        calib.Branch("time_PSD1", buf.fPSD_t2, "time_PSD1/F")
        calib.Branch("MaxQ_2inchPMT", buf.f2inch_maxQ, "MaxQ_2inchPMT/F")
        return calib, buf

    @staticmethod
    def prep_reco(TTree, host_file, name):
        """Create the "reco" (~AdSimple) TTree and fill buffer.

        Return a tuple of (adSimple, buffer) containing the TTree object and the
        buffer used to fill its TBranches.
        """
        buf = util.TreeBuffer()
        buf.triggerType = util.unsigned_int_value()
        buf.site = util.int_value()
        buf.energy = util.float_value()
        buf.x = util.float_value()
        buf.y = util.float_value()
        buf.z = util.float_value()

        host_file.cd()
        event_subdir = host_file.Get("Event")
        if not bool(event_subdir):
            event_subdir = host_file.mkdir("Event")
        event_subdir.cd()
        rec_subdir = event_subdir.Get("Rec")
        if not bool(rec_subdir):
            rec_subdir = event_subdir.mkdir("Rec")
        rec_subdir.cd()
        long_name = "Tree at /Event/Rec/{name} holding Rec_{name}".format(name=name)
        reco = TTree(name, long_name)
        reco.Branch("context.mSite", buf.site, "context.mSite/I")
        reco.Branch("triggerType", buf.triggerType, "triggerType/i")
        reco.Branch("energy", buf.energy, "energy/F")
        reco.Branch("x", buf.x, "x/F")
        reco.Branch("y", buf.y, "y/F")
        reco.Branch("z", buf.z, "z/F")
        return reco, buf


class EventType(ABC):
    """The base class for different event types."""

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def generate_events(self, rng, duration_s):
        """Generate a list of Event objects for the given duration."""
        return []

    @staticmethod
    def actual_event_count(rng, duration_s, rate_hz):
        """Generate an actual event count given the rate and duration."""
        expected_count = duration_s * rate_hz
        return rng.poisson(expected_count)


Event = namedtuple(
    "Event",
    [
        "trigger_number",
        "timestamp",
        "detector",
        "trigger_type",
        "site",
        "energy",
        "nHit",
        "charge",
        "x",
        "y",
        "z",
        "fMax",
        "fQuad",
        "fPSD_t1",
        "fPSD_t2",
        "f2inch_maxQ",
    ],
)


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
    from single import Single
    from correlated import Correlated
    from muon import Muon

    parser = argparse.ArgumentParser(description="Daya Bay Toy MC by Sam Kohn")
    parser.add_argument("outfile")
    parser.add_argument("-t", "--runtime", type=int)
    parser.add_argument("-s", "--seed", default=None, type=int)
    args = parser.parse_args()
    main(args.outfile, args.runtime, args.seed)
