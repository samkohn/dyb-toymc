"""Define the muon event type."""

import toymc


class Muon(toymc.EventType):
    """Muon event type including all different types of muons."""

    def __init__(self, name, site, rate_Hz):
        super().__init__(name)
        self.rate_hz = rate_Hz
        self.site = site
        self.avail_ads = {1: (1, 2), 2: (1, 2), 3: (1, 2, 3, 4)}[site]
        self.prob_WP_no_AD = 0.8
        self.prob_WP_and_AD = 0.1995
        self.prob_WP_and_shower = 0.0005
        self.WP_detector = 6
        self.trigger_type = 0x10001100
        self.WP_nHit_spectrum = lambda rng: rng.integers(15, 100)
        self.ADMuon_energy_spectrum = lambda rng: rng.uniform(20, 2000)
        self.shower_energy_spectrum = lambda rng: rng.uniform(2500, 5000)

    def generate_events(self, rng, duration_s):
        actual_number = self.actual_event_count(rng, duration_s, self.rate_hz)
        number_admuons = int(actual_number * self.prob_WP_and_AD)
        number_showermuons = int(actual_number * self.prob_WP_and_shower)
        duration_ns = int(1e9) * duration_s
        times_WP = rng.integers(0, duration_ns, size=actual_number)
        ad_delay = 50
        events = []
        # First generate all WP events:
        for time_WP in times_WP:
            wp_event = self.new_WP_event(rng, time_WP)
            events.append(wp_event)
        # Next generate associated AD Muon events
        for time_WP in times_WP[:number_admuons]:
            ad_event = self.new_AD_event(rng, time_WP + ad_delay)
            events.append(ad_event)
        # Next generate associated shower muon events
        for time_WP in times_WP[number_admuons : (number_admuons + number_showermuons)]:
            shower_event = self.new_shower_event(rng, time_WP + ad_delay)
            events.append(shower_event)
        return events

    def new_WP_event(self, rng, timestamp):
        """Generate a new WP Muon event with the given timestamp."""
        event = toymc.Event(
            1,
            timestamp,
            self.WP_detector,
            self.trigger_type,
            self.site,
            *self.WP_physical_quantities(rng),
        )
        return event

    def new_AD_event(self, rng, timestamp):
        """Generate a new AD Muon event with the given timestamp."""
        event = toymc.Event(
            1,
            timestamp,
            rng.choice(self.avail_ads),
            self.trigger_type,
            self.site,
            *self.AD_muon_physical_quantities(rng),
        )
        return event

    def new_shower_event(self, rng, timestamp):
        """Generate a new shower muon event with the given timestamp."""
        event = toymc.Event(
            1,
            timestamp,
            rng.choice(self.avail_ads),
            self.trigger_type,
            self.site,
            *self.shower_muon_physical_quantities(rng),
        )
        return event

    def WP_physical_quantities(self, rng):
        """Generate the physical quantities for a WP event."""
        energy = 0
        nHit = self.WP_nHit_spectrum(rng)
        charge = 0
        x = 0
        y = 0
        z = 0
        fMax = 0
        fQuad = 0
        fPSD_t1 = 0
        fPSD_t2 = 0
        f2inch_maxQ = 0
        return (
            energy,
            nHit,
            charge,
            x,
            y,
            z,
            fMax,
            fQuad,
            fPSD_t1,
            fPSD_t2,
            f2inch_maxQ,
        )

    def AD_muon_physical_quantities(self, rng):
        """Generate the physical quantities for an AD Muon event."""
        physical_energy = self.ADMuon_energy_spectrum(rng)
        pe_per_mev = 170
        charge = physical_energy * pe_per_mev
        nHit = 192
        x = 0
        y = 0
        z = 0
        fMax = 0.1
        fQuad = 0.1
        fPSD_t1 = 0.99
        fPSD_t2 = 0.99
        f2inch_maxQ = 0
        return (
            physical_energy,
            nHit,
            charge,
            x,
            y,
            z,
            fMax,
            fQuad,
            fPSD_t1,
            fPSD_t2,
            f2inch_maxQ,
        )

    def shower_muon_physical_quantities(self, rng):
        """Generate the physical quantities for a shower muon event."""
        physical_energy = self.shower_energy_spectrum(rng)
        pe_per_mev = 170
        charge = physical_energy * pe_per_mev
        nHit = 192
        x = 0
        y = 0
        z = 0
        fMax = 0.1
        fQuad = 0.1
        fPSD_t1 = 0.99
        fPSD_t2 = 0.99
        f2inch_maxQ = 0
        return (
            physical_energy,
            nHit,
            charge,
            x,
            y,
            z,
            fMax,
            fQuad,
            fPSD_t1,
            fPSD_t2,
            f2inch_maxQ,
        )
