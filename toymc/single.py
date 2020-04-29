"""The simplest event type is the Single uncorrelated AD event.

Each single event is generated totally independently with no time or
position correlations to other events. This makes the ``Single`` a good
event type to use to represent the uncorrelated singles in the Daya Bay
ADs.

As specified in the API below, there are user-configurable options
for this event type. The simplest, barely worth mentioning, is the
:py:attr:`~Single.trigger_type` attribute, which you can use to change
the trigger type of the events. It is a simple number and so you can't
use any randomness for it.

The first real configurable is the :py:attr:`~Single.energy_spectrum`.
This function is called to generate a value for the event energy.
To replace it, define your own function that accepts a random
number generator (RNG) as its only argument, and uses the RNG to
generate and return an energy value. Then assign the function to the
``energy_spectrum`` attribute, like so::

    >>> single.energy_spectrum = my_energy_function

The other configurable is :py:attr:`~Single.position_spectrum_mm`.
This function is called to generate the (x, y, z) position for each
event (**in millimeters**). Because generating random positions
within a cylindrical volume is not trivial, there are some helper
functions available in the :py:mod:`toymc.util` module that help
apply boundaries to the randomly-generated values. Check out
:py:func:`toymc.util.rng_uniform_cylinder` for an example of how to use
the helper functions.
"""

import toymc
import toymc.util as util


class Single(toymc.EventType):
    """Single events occur uniformly at random.

    Parameters
    ----------
    name : str
        The human-readable name of this event type
    rate_Hz : number
        The single event rate, **in hertz**
    site : number
        The EH code for this event type (1, 2, or 4)
    detector : number
        The detector (AD) code for this event type (1, 2, 3, or 4)

    Attributes
    ----------
    trigger_type : number
        The value to use for the :py:attr:`toymc.Event.trigger_type` in
        Events created by this object. Default: ``0x10001100``.
    energy_spectrum : function(rng) -> number
        The energy generator function. Default: uniform between
        1 and 3.5.
    position_spectrum_mm : function(rng) -> (number, number, number)
        The position generator function, **in millimeters**. Default: uniform
        within a 4m x 4m cylinder.
    """

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
        """Generate single uncorrelated events over the given duration.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.
        """
        actual_number = self.actual_event_count(rng, duration_s, self.rate_hz)
        duration_ns = int(1e9) * duration_s
        events = []
        timestamps = rng.integers(0, duration_ns, size=actual_number)
        for timestamp in timestamps:
            event = self.new_event(rng, timestamp)
            events.append(event)
        return events

    def new_event(self, rng, timestamp):
        """Generate a new Event object with the given timestamp.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.

        This method begins constructing an Event object and delegates
        the complicated parts to :py:meth:`Single.physical_quantities`.
        """
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
        """Generate the physical quantities for a single event.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.

        This method determines the energy and position of the single
        event using :py:attr:`Single.energy_spectrum` and
        :py:attr:`Single.position_spectrum_mm`, respectively.
        """
        physical_energy = self.energy_spectrum(rng)
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
