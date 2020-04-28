"""Define single AD events."""

import toymc
import toymc.util as util


class Single(toymc.EventType):
    """Single events occur uniformly at random."""

    def __init__(self, name, rate_Hz, site, detector):
        super().__init__(name)
        self.rate_hz = rate_Hz
        self.site = site
        self.detector = detector
        self.trigger_type = 0x10001100
        self.energy_spectrum = lambda rng: rng.uniform(1, 3.5)
        default_radius = 2000
        self.position_spectrum_mm = util.rng_uniform_cylinder(
            default_radius, 2 * default_radius
        )

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

    def physical_quantities(self, rng):
        """Generate the physical quantities for a single event."""
        physical_energy = rng.uniform(1, 3.5)
        physical_x, physical_y, physical_z = self.position_spectrum_mm(rng)
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
