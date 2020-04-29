"""The Muon event type tries to encapsulate some of the complex
correlations among muon events.

Each muon in this model hits the outer water pool (WP, ``detector=6``),
and then potentially also causes an AD muon event or a shower muon
event. For simplicity, AD and shower muon events are assigned positions
at the origin (center of the AD). Future versions may have a more
sophisticated/realistic model of these hit correlations (e.g. including
the IWS, or allowing for AD muons that don't have a correlated WP hit).

There are a much larger number of configurables for this event type due
to the complexity of the situation being modeled. Of course there is
still the trigger type.

The 3 ``prob_*`` attributes control the probabilities of a WP muon
missing the ADs, or also causing an AD muon event or a showering muon
event. They should add to 1, but any deviation from 1 is added to or
taken from the :py:attr:`~Muon.prob_WP_no_AD` value. (E.g. if they sum
to 0.95, then the probability of a WP event but no AD event is
effectively incremented by 0.05.) But really. Just make them sum to 1!

There are also 3 ``*_spectrum`` attributes which control the spectra for
the 3 types of muons (WP, AD, and shower). The oddball is
:py:attr:`~Muon.WP_nHit_spectrum`, because the WP events do not go
through an energy reconstruction, and the WP Muon cuts are based on
nHit. So the function assigned to that attribute should **return an
integer, not a float**. The spectra for events in the AD have the usual
signature and return energies, not nHits.

Lastly, :py:attr:`~Muon.avail_ads` is a tuple specifying which AD
detector values (1, 2, 3, and/or 4) are available when randomly choosing
which AD will get a given AD muon or shower muon.
"""

import toymc


class Muon(toymc.EventType):
    """Muon event type including all different types of muons.

    Parameters
    ----------
    name : str
        The human-readable name of this event type
    site : number
        The EH code for this event type (1, 2, or 4)
    rate_Hz : number
        The rate for WP muons to appear, **in hertz**

    Attributes
    ----------
    trigger_type : number
        The value to use for the :py:attr:`toymc.Event.trigger_type` in
        Events created by this object. Default: ``0x10001100``.
    prob_WP_no_AD : number
        The probability that a given muon hits only the WP
    prob_WP_and_AD : number
        The probability that a given muon hits the WP and also causes an
        AD muon event
    prob_WP_and_shower : number
        The probability that a given muon hits the WP and also causes a
        shower muon event
    WP_nHit_spectrum : function(rng) -> int
        The generator for determining the nHit value for WP events.
        Default: uniform integer between 15 and 100, inclusive.
    ADMuon_energy_spectrum : function(rng) -> number
        The AD muon energy generator function. Default: uniform
        between 20 and 2000.
    shower_energy_spectrum : function(rng) -> number
        The shower muon energy generator function. Default: uniform
        between 2500 and 5000.
    avail_ads : tuple
        The available ADs (1, 2, 3, and/or 4) to choose between when
        determining which AD gets any given AD muon or shower muon.
        Default: (1, 2) for sites 1 and 2; (1, 2, 3, 4) for site 4.
        Error if any other site is given.
    """

    def __init__(self, name, site, rate_Hz):
        super().__init__(name)
        self.rate_hz = rate_Hz
        self.site = site
        self.avail_ads = {1: (1, 2), 2: (1, 2), 4: (1, 2, 3, 4)}[site]
        self.prob_WP_no_AD = 0.8
        self.prob_WP_and_AD = 0.1995
        self.prob_WP_and_shower = 0.0005
        self.WP_detector = 6
        self.trigger_type = 0x10001100
        self.WP_nHit_spectrum = lambda rng: rng.integers(15, 100)
        self.ADMuon_energy_spectrum = lambda rng: rng.uniform(20, 2000)
        self.shower_energy_spectrum = lambda rng: rng.uniform(2500, 5000)

    def generate_events(self, rng, duration_s):
        """Generate muon events over the given duration.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.
        """
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
        """Generate a new WP Muon event with the given timestamp.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.

        This method begins constructing an Event
        object and delegates the complicated parts to
        :py:meth:`Muon.WP_physical_quantities`.
        """
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
        """Generate a new AD Muon event with the given timestamp.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.

        This method begins constructing an Event
        object and delegates the complicated parts to
        :py:meth:`Muon.AD_muon_physical_quantities`.
        """
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
        """Generate a new shower muon event with the given timestamp.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.

        This method begins constructing an Event
        object and delegates the complicated parts to
        :py:meth:`Muon.shower_muon_physical_quantities`.
        """
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
        """Generate the physical quantities for a WP event.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.

        This method determines the nHit value of the WP
        event using :py:attr:`~Muon.WP_nHit_spectrum`.
        """
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
        """Generate the physical quantities for an AD Muon event.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.

        This method determines the energy of the AD muon
        event using :py:attr:`~Muon.ADMuon_energy_spectrum`.
        """
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
        """Generate the physical quantities for a shower muon event.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.

        This method determines the energy of the shower muon
        event using :py:attr:`~Muon.shower_energy_spectrum`.
        """
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
