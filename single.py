"""Define single AD events."""

import math

import toymc


class Single(toymc.EventType):
    """Single events occur uniformly at random."""

    def __init__(self, name, rate_Hz, site, detector, trigger_type):
        super().__init__(name)
        self.rate_hz = rate_Hz
        self.site = site
        self.detector = detector
        self.trigger_type = trigger_type

    def generate_events(self, rng, duration_s):
        actual_number = self.actual_event_count(rng, duration_s, self.rate_hz)
        duration_ns = int(1e9) * duration_s
        events = []
        timestamps = rng.integers(0, duration_ns, size=actual_number)
        for timestamp in timestamps:
            event = self.new_event(rng, timestamp)
            events.append(event)
        return events

    def new_event(self, rng, timestamp):
        """Generate a new Event object with the given timestamp."""
        event = toymc.Event(
            1,
            timestamp,
            self.detector,
            self.trigger_type,
            self.site,
            *self.physical_quantities(rng),
        )
        return event

    @staticmethod
    def physical_quantities(rng):
        """Generate the physical quantities for a single event."""
        # pylint: disable=invalid-name
        physical_energy = rng.uniform(1, 3.5)
        physical_x = 50
        physical_y = 50
        while math.hypot(physical_x, physical_y) > 2:
            physical_x, physical_y = rng.uniform(-2, 2, size=2)
        physical_z = rng.uniform(-2, 2)
        pe_per_mev = 170
        charge = physical_energy * pe_per_mev
        nHit = 192
        fMax = 0.1
        fQuad = 0.1
        fPSD_t1 = 0.99
        fPSD_t2 = 0.99
        f2inch_maxQ = 0
        return (
            physical_energy,
            nHit,
            charge,
            physical_x,
            physical_y,
            physical_z,
            fMax,
            fQuad,
            fPSD_t1,
            fPSD_t2,
            f2inch_maxQ,
        )
