"""Define a simple correlated event type."""

import math

import toymc


class Correlated(toymc.EventType):
    """Correlated event type with exponential decay between prompt and delayed."""

    def __init__(self, name, site, detector, rate_Hz, coincidence_ns):
        super().__init__(name)
        self.rate_hz = rate_Hz
        self.site = site
        self.detector = detector
        self.trigger_type = 0x10001100
        self.coincidence_ns = coincidence_ns

    def generate_events(self, rng, duration_s):
        actual_number = self.actual_event_count(rng, duration_s, self.rate_hz)
        duration_ns = int(1e9) * duration_s
        events = []
        times_prompt = rng.integers(0, duration_ns, size=actual_number)
        delays = rng.exponential(1 / self.coincidence_ns, size=actual_number).astype(
            int
        )
        times_delayed = times_prompt + delays
        for time_prompt, time_delayed in zip(times_prompt, times_delayed):
            prompt = self.new_prompt_event(rng, time_prompt)
            events.append(prompt)
            delayed = self.new_delayed_event(rng, time_delayed)
            events.append(delayed)
        return events

    def new_prompt_event(self, rng, timestamp):
        """Generate a new prompt Event object with the given timestamp."""
        event = toymc.Event(
            1,
            timestamp,
            self.detector,
            self.trigger_type,
            self.site,
            *self.prompt_physical_quantities(rng),
        )
        return event

    def new_delayed_event(self, rng, timestamp):
        """Generate a new delayed Event object with the given timestamp."""
        event = toymc.Event(
            1,
            timestamp,
            self.detector,
            self.trigger_type,
            self.site,
            *self.delayed_physical_quantities(rng),
        )
        return event

    @staticmethod
    def prompt_physical_quantities(rng):
        """Generate the physical quantities for a prompt event."""
        # pylint: disable=invalid-name
        physical_energy = rng.uniform(0.7, 4)
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

    @staticmethod
    def delayed_physical_quantities(rng):
        """Generate the physical quantities for a delayed event."""
        # pylint: disable=invalid-name
        physical_energy = rng.uniform(7, 9)
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
