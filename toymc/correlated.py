"""The Correlated event type is a basic but powerful model of
correlated-pair events.

Each event pair is generated independently from other pairs. The
prompt and delayed energies are independent, but the time delay is
sampled from an exponential distribution, and the delayed position is
user-configurable, but defaults to an exponential distribution in terms
of displacement from the prompt event.

There are 2 ``MCTruthLookup`` labels for Correlated events: one for the
prompt and one for the delayed:

- text labels: append ``"_prompt"`` and ``"_delayed"`` to the name
  provided to this class in the constructor
- numeric lookup: the value of ``self.truth_label_prompt`` and
  ``self.truth_label_delayed``, respectively

The user-configurable options specified below include, as usual,
:py:attr:`~Correlated.trigger_type` and then some interesting ones.

First, the :py:attr:`~Correlated.prompt_energy_spectrum` and
:py:attr:`~Correlated.delayed_energy_spectrum`. These attributes should
be functions of a single parameter (the RNG) that return a single
value (each) representing the energy of the prompt and delayed events,
respectively.

Next, the :py:attr:`~Correlated.prompt_position_spectrum_mm`, which
generates the position of each prompt event (**in millimeters**). The
default is a uniform distribution within a 3m x 3m cylinder.

Lastly, the :py:attr:`~Correlated.delayed_pos_from_prompt_mm`, which
generates the position of each delayed event (**in millimeters**) given
the position of the correlated prompt event. So that function takes
2 arguments: the RNG, and then a 3-tuple ``(x, y, z)`` of the prompt
position, and returns a 3-tuple of the generated delayed position.

The helper functions in :py:mod:`toymc.util` may be helpful
when you go to create your own sophisticated generators. See
:py:func:`toymc.util.rng_correlated_expo_cylinder` for an example of how
to connect all the parts together.
"""

import toymc
import toymc.util as util


class Correlated(toymc.EventType):
    """Correlated event type with exponential decay between prompt and delayed.

    Parameters
    ----------
    name : str
        The human-readable name of this event type
    site : number
        The EH code for this event type (1, 2, or 4)
    detector : number
        The detector (AD) code for this event type (1, 2, 3, or 4)
    rate_Hz : number
        The rate for pairs to appear (equivalently, the prompt rate,
        or the rate of the physical process that produces pairs),
        **in hertz**
    coincidence_ns : number
        The coincidence time scale to use for the exponential
        distribution that determines the delay between prompt and
        delayed events, **in nanoseconds**

    Attributes
    ----------
    truth_label_prompt : positive integer
        The code for the prompt event subtype in the MC Truth records.
        Default: ``None``.
    truth_label_delayed : positive integer
        The code for the delayed event subtype in the MC Truth records.
        Default: ``None``.
    trigger_type : number
        The value to use for the :py:attr:`toymc.Event.trigger_type` in
        Events created by this object. Default: ``0x10001100``.
    prompt_energy_spectrum : function(rng) -> number
        The prompt energy generator function. Default: uniform
        between 0.7 and 4.
    delayed_energy_spectrum : function(rng) -> number
        The delayed energy generator function. Default: uniform
        between 7 and 9.
    prompt_position_spectrum_mm : function(rng) -> (x, y, z)
        The prompt position generator function, **in millimeters**.
        Default: uniform within a 3m x 3m cylinder.
    delayed_pos_from_prompt_mm : function(rng, (x, y, z)) -> (x, y, z)
        The delayed position generator function, **in millimeters**.
        This function has available both the RNG and the prompt position
        (**in millimeters**) to allow for position correlations.
        Default: x, y, z displaced by samples from an exponential
        distribution with scale of 50mm, restricted to within the 3m x
        3m cylinder.
    """

    def __init__(self, name, site, detector, rate_Hz, coincidence_ns):
        super().__init__(name)
        self.rate_hz = rate_Hz
        self.site = site
        self.detector = detector
        self.trigger_type = 0x10001100
        self.coincidence_ns = coincidence_ns
        self.prompt_energy_spectrum = lambda rng: rng.uniform(0.7, 4)
        self.delayed_energy_spectrum = lambda rng: rng.uniform(7, 9)
        default_prompt_delayed_distance_mm = 50
        default_radius = 1500
        self.prompt_position_spectrum_mm = util.rng_uniform_cylinder(
            default_radius, 2 * default_radius
        )
        self.delayed_pos_from_prompt_mm = util.rng_correlated_expo_cylinder(
            default_radius, 2 * default_radius, default_prompt_delayed_distance_mm
        )
        self.truth_label_prompt = None
        self.truth_label_delayed = None

    def generate_events(self, rng, duration_s, t0_s):
        """Generate correlated events over the given duration.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.
        """
        actual_number = self.actual_event_count(rng, duration_s, self.rate_hz)
        duration_ns = int(1e9) * duration_s
        start_ns = int(1e9) * t0_s
        end_ns = start_ns + duration_ns
        events = []
        times_prompt = rng.integers(start_ns, end_ns, size=actual_number)
        delays = rng.exponential(1 / self.coincidence_ns, size=actual_number).astype(
            int
        )
        times_delayed = times_prompt + delays
        for time_prompt, time_delayed in zip(times_prompt, times_delayed):
            prompt = self.new_prompt_event(rng, time_prompt)
            events.append(prompt)
            prompt_position = (prompt.x, prompt.y, prompt.z)
            delayed = self.new_delayed_event(rng, time_delayed, prompt_position)
            events.append(delayed)
        return events

    def labels(self):
        """Return a labels dict mapping the lookup numbers to prompt and
        delayed."""
        return {
            self.truth_label_prompt: "{}_prompt".format(self.name),
            self.truth_label_delayed: "{}_delayed".format(self.name),
        }

    def new_prompt_event(self, rng, timestamp):
        """Generate a new prompt Event object with the given timestamp.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.

        This method begins constructing an Event
        object and delegates the complicated parts to
        :py:meth:`Correlated.prompt_physical_quantities`.
        """
        event = toymc.Event(
            self.truth_label_prompt,
            1,
            timestamp,
            self.detector,
            self.trigger_type,
            self.site,
            *self.prompt_physical_quantities(rng),
        )
        return event

    def new_delayed_event(self, rng, timestamp, prompt_position):
        """Generate a new delayed Event object with the given timestamp.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.

        This method begins constructing an Event
        object and delegates the complicated parts to
        :py:meth:`Correlated.delayed_physical_quantities`.
        """
        event = toymc.Event(
            self.truth_label_delayed,
            1,
            timestamp,
            self.detector,
            self.trigger_type,
            self.site,
            *self.delayed_physical_quantities(rng, prompt_position),
        )
        return event

    def prompt_physical_quantities(self, rng):
        """Generate the physical quantities for a prompt event.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.

        This method determines the energy and position of the prompt
        event using :py:attr:`~Correlated.prompt_energy_spectrum` and
        :py:attr:`~Correlated.prompt_position_spectrum_mm`, respectively.
        """
        physical_energy = self.prompt_energy_spectrum(rng)
        physical_x, physical_y, physical_z = self.prompt_position_spectrum_mm(rng)
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

    def delayed_physical_quantities(self, rng, prompt_position):
        """Generate the physical quantities for a delayed event.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.

        This method determines the energy and position of the delayed
        event using :py:attr:`~Correlated.delayed_energy_spectrum` and
        :py:attr:`~Correlated.delayed_pos_from_prompt_mm`, respectively.
        """
        physical_energy = self.delayed_energy_spectrum(rng)
        physical_x, physical_y, physical_z = self.delayed_pos_from_prompt_mm(
            rng, prompt_position
        )
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
