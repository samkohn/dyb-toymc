"""This Toy Monte Carlo is designed to produce simulated data streams
consisting of known rates of various event types such as singles,
correlated pairs / IBDs, and muons.

The steps for generating this data stream are relatively simple:

    1. Determine how many events of each type to produce
    2. For each event, produce timestamps uniformly at random within the
       given data-taking time window.
    3. Then generate physical quantities for each event according to the
       instructions provided for each particular event type.
    4. For correlated event chains, generate the time delay for delayed
       events and repeat steps 3 and 4 until all desired events have been
       generated.
    5. Aggregate all events into a list, sort by timestamp, and save
       to a file.

Physically-correlated events (e.g. prompt-delayed or WPMuon-ADMuon) are
treated as a single event type. Their occurrence is determined by the
rate of the physical process that causes the correlated events (e.g.
an IBD interaction, or a muon). For each physical event, the presence
and properties of the actual "triggered events" (i.e. TTree entries)
can be determined, perhaps using some randomness. For example, for the
:py:class:`.Correlated` event type, first the number of prompt-delayed
pairs is determined given the process event rate and data stream
duration. Timestamps for the prompt events are then assigned uniformly
at random. Then, the time delay between prompt and delayed is determined
by sampling an exponential distribution independently for each prompt
event. The position (correlated between prompt and delayed) is similarly
determined for each delayed event based on the corresponding prompt
event's position. This treatment is sufficient to handle the variety of
correlations that appear in the Daya Bay data stream.

Because Daya Bay data files use the ROOT format, this Toy Monte Carlo
only outputs ROOT files.

Running the Toy Monte Carlo
---------------------------

To run the Toy Monte Carlo, create a new script that will contain your
particular configuration. Import :py:mod:`toymc` as well as any event
type classes you'll be using.

To start, you'll need to initialize the :py:class:`ToyMC` object with
your output file location, the DAQ runtime, and optionally a random
seed. You can also customize the name of the output TTrees from their
defaults of ``reco_name="AdSimpleNL"`` and ``calib_name="CalibStats"``.

Next, initialize the event types you'll be using. The built-in
event types are :py:class:`.Single` (uncorrelated events),
:py:class:`.Correlated` (correlated pairs), and :py:class:`Muon` (WP, AD
and Shower muons, and, potentially in a future version, muon-correlated
backgrounds). Each comes with a default configuration that can be
adjusted. For example, you may want to supply a different energy
spectrum or position distribution. More on the interface for specifying
custom distributions later.

Now you need to add the event type objects to the :py:class:`ToyMC`
execution object using the :py:meth:`ToyMC.add_event_type` method.

Lastly, run the Toy Monte Carlo by calling the :py:meth:`ToyMC.run`
method. The output file is automatically saved and closed at the end of
execution.

For a simple working example with all the different event types, see
example.py in the dyb-toymc repository.

Recording the true event types
------------------------------

The Toy MC saves the "true" event type for each event so that you can
see if your analysis code correctly recognizes different types of
events. The truth information corresponding to each output TTree entry
is saved in its own TTree located at ``/MCTruth`` directly in the output
file. A lookup table/legend is also saved to ``/MCTruthLookup``.

For clarity, I will refer to the different Python classes that subclass
:py:class:`EventType` as "event types," and to the different possible
types of triggered readout events (e.g. prompt, delayed, WP muon, AD
muon) as "event subtypes."

Each event type can consist of multiple subtypes. For example, the
:py:class:`~toymc.correlated.Correlated` event type has 2 subtypes:
prompt and delayed. The event type class is responsible for enumerating
its own event subtypes and providing a mechanism to assign lookup
numbers to each of them. (Suggested mechanism is just the object
attributes, e.g. ``my_event.first_subclass_label = 5``.) These lookup
numbers will be filled into the corresponding entries in the ``MCTruth``
output TTree as the truth record for each subevent. **As the user, you
must assign a lookup number to every single subevent type present in all
of the EventType objects you create.** This includes if you initialize
multiple objects from a single EventType class --- each object needs to
get its own unique lookup numbers. The Toy MC will *not* do this for
you.

I firmly believe that if you send someone a data file, they should be
able to figure out what most of the data means just from the information
within the file. (Maybe let's go easy on ourselves and limit the list of
recipients to other Daya Bay analyzers.) Practically, what this means
is that using arbitrary numbers to represent data types is insufficient
without a lookup table. And as mentioned prevously, the Toy MC provides
a lookup table in the form of a TTree saved to ``/MCTruthLookup``.

The MCTruthLookup TTree contains a bi-directional lookup, both from
textual labels to subtype numbers, and vice versa. To build this
table, the Toy MC calls the :py:meth:`EventType.labels` method from the
corresponding event type. This method gives a dict that associates a
string label (should be only alphanumerics + underscore) to the lookup
number for each event subtype. The labels for the built-in event type
subtypes are built up from the instance's ``name`` attribute, and any
custom EventType classes you define should do the same.

.. note:: If the name you give when you construct a new EventType
   object is not a valid Python variable name (e.g. if it has a space in
   it), then you will not be able to use the PyROOT shortcut of accessing
   the corresponding TBranch using ``my_tree.branch_name``. You will
   still be able to access the TBranch in C++ and in Python using the
   ``SetBranchAddress`` pattern. This isn't a huge problem because I
   anticipate most usage of MCTruthLookup will be via
   ``MCTruthLookup->Show(0)`` in the interactive ROOT prompt.

The lookup table is implemented as the list of TBranches on the TTree.
So for example, if, as before, ``my_event.first_subclass_label = 5``,
and the associated text label is ``'first_event_type'``,
then there will be a TBranch with name ``5`` that will be assigned a
C string value of ``"first_event_type"``, and also a TBranch with name
``"first_event_type"`` that will be assigned an ``unsigned int`` value
of 5. This TTree will only have 1 "entry" since the variety of events
are encoded in the TBranches rather than the entries.

Here's an example output showing an MCTruthLookup table. The named
TBranches are sorted alphabetically, and the numbered ones are sorted
numerically::

    root [1] MCTruthLookup->Show(0)
    ======> EVENT:0
     IBD_nGd_delayed = 2
     IBD_nGd_prompt  = 1
     Single_event    = 0
     _0              = Single_event
     _1              = IBD_nGd_prompt
     _2              = IBD_nGd_delayed

Customizing the random generators
---------------------------------

Each event type class relies on functions stored as instance attributes
to characterize the physical quantities that are generated by the Toy
Monte Carlo. I say "functions stored as instance attributes" rather
than "instance methods" because these functions are intended to be
replaced by you, the user, and they don't take ``self`` as an argument.
They also are not defined by the class using ``def`` syntax like an
instance method normally would. Instead they're instantiated to a
default (function) value in the ``__init__`` method, just like any other
instance attribute.

Although the exact function signatures differ slightly depending on
the needs of each event type, they all follow a similar pattern that is
easy to adapt for custom energy spectra, position distributions, etc.

Internally, when a given quantity such as event energy is needed, the
Toy Monte Carlo will look up the appropriate instance attribute and
call the function, supplying as the first parameter a random number
generator (RNG) object (for example, ``obj.energy_spectrum(rng)``).
The ``rng`` object is an instance of the ``numpy.random.Generator``
class, and documentation on available methods can be found online:
<https://numpy.org/doc/stable/reference/random/generator.html>. It is
the responsibility of the function to call whatever random number
generation methods using the ``rng`` parameter, assemble them in some
fancy way, and return the desired value.

.. warning::
   do *not* create your own random generator instance via NumPy or the
   Python random module. The ToyMC library creates a single internal RNG
   that is used for all random number generation.

To customize the behavior (again, for an example, the energy spectrum),
simply define your own function that takes ``rng`` as a parameter and
does what you want with it. For example, here is a simplistic
configuration for an event type that looks like IBD with neutron capture
on hydrogen (nH)::

    >>> ibd_nH = Correlated("IBD nH", 1, 1, 0.006, 150000)
    >>> def nH_delayed_spectrum(rng):  # It's not perfect, but
    >>>     return rng.uniform(1.9, 2.3)  # at least the range is right!
    >>> ibd_nH.delayed_energy_spectrum = nH_delayed_spectrum

Now each time the Toy Monte Carlo needs a value for an nH delayed
energy, it will run the function ``nH_delayed_spectrum`` and supply the
RNG. The returned value in this case is simply chosen uniformly at
random, but it could be quite complicated, e.g. weighted by a histogram.

The documentation for each built-in class specifies the available
attributes that can be customized. A small number of helper methods are
available in the :py:mod:`toymc.util` module.

Creating new event types
------------------------

New event types are easily created by creating a subclass of
:py:class:`toymc.EventType`. You should override ``__init__`` and
``generate_events``. In the latter method, you should include whatever
logic you need to generate your events. You will be provided with a
random number generator (instance of numpy.random.Generator) as the
first parameter. In the built-in event types, most of the logic is
specified in sub-methods to help keep the code clean and readable.

Each event you create (i.e. each element of the list returned by
``generate_events`` must be an instance of :py:class:`toymc.Event`,
which is a ``namedtuple`` class. When you construct these Event objects,
you must provide all 16 attributes in the correct order. They are
also immutable, so you cannot change values from an existing Event
object. You shouldn't have to, though, if you follow the pattern for
generating events from the built-in event types. See the :py:class:`API
documentation for Event <toymc.Event>` for more details.
"""
import argparse
from collections import namedtuple
from operator import attrgetter
from abc import ABC, abstractmethod
from numpy.random import default_rng
import numpy as np

import root_util


class ToyMC:
    """The ToyMC top-level manager class.

    This is the class you should create first when you want to set up a
    Toy Monte Carlo script.

    Parameters
    ----------
    outfile : str
        The file name/location for the output ROOT file
    duration : number
        The duration of data taking to generate data for, **in seconds**

    Keyword Arguments
    -----------------
    reco_name : str
        The name of the TTree containing reconstructed data located at
        /Event/Rec
    calib_name : str
        The name of the TTree containing the calibrated statistics data
        located at /Event/Data
    seed : int
        The seed to use for the random number generator. If ``None`` or
        not specified, the random number generator will use a seed
        generated by the system.
    """

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
            self.outfile, self.reco_name, self.calib_name, self.event_types,
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
    """The ToyMC output data structure (internal class).

    This class is used internally to prepare and fill the output ROOT
    TTrees.

    The required ``event_types`` parameter is necessary to generate the
    MC Truth lookup TTree.

    Parameters
    ----------
    container : ROOT.TFile
        The ``TFile`` that will host the ToyMC output data structures
    reco_name : str
        The name of the reconstructed data TTree
    calib_name : str
        The name of the calibrated statistics TTree
    event_types : list of :py:class:`EventType`
        The list of EventType objects to add to the lookup table
    """

    def __init__(self, container, reco_name, calib_name, event_types):
        from ROOT import TTree  # pylint: disable=no-name-in-module

        self.container = container
        self.container.cd()
        self.reco_ttree, self.reco_buf = self.prep_reco(
            TTree, self.container, reco_name
        )
        self.calib_ttree, self.calib_buf = self.prep_calib(
            TTree, self.container, calib_name
        )
        self.truth_ttree, self.truth_buf = self.prep_truth(TTree, self.container)
        self.truth_lookup_ttree, _ = self.prep_truth_lookup(
            TTree, self.container, event_types
        )

    def add(self, event):
        """Add the given event to the output data structure.

        Parameters
        ----------
        event : :py:class:`Event`
            The event to fill into the ToyMC output
        """
        rb = self.reco_buf
        cb = self.calib_buf
        assign_value = root_util.assign_value
        assign_value(cb.triggerNumber, event.trigger_number)
        assign_value(cb.detector, event.detector)
        timestamp_seconds = event.timestamp // 1000000000
        timestamp_nanoseconds = event.timestamp % 1000000000
        assign_value(cb.timestamp_seconds, timestamp_seconds)
        assign_value(cb.timestamp_nanoseconds, timestamp_nanoseconds)
        assign_value(cb.nHit, event.nHit)
        assign_value(cb.charge, event.charge)
        assign_value(cb.fQuad, event.fQuad)
        assign_value(cb.fMax, event.fMax)
        assign_value(cb.fPSD_t1, event.fPSD_t1)
        assign_value(cb.fPSD_t2, event.fPSD_t2)
        assign_value(cb.f2inch_maxQ, event.f2inch_maxQ)

        assign_value(rb.triggerType, event.trigger_type)
        assign_value(rb.site, event.site)
        assign_value(rb.energy, event.energy)
        assign_value(rb.x, event.x)
        assign_value(rb.y, event.y)
        assign_value(rb.z, event.z)

        assign_value(self.truth_buf.truth_label, event.truth_label)

        self.reco_ttree.Fill()
        self.calib_ttree.Fill()
        self.truth_ttree.Fill()

    @staticmethod
    def prep_calib(TTree, host_file, name):
        """Create the "calib" (~CalibStats) TTree and fill buffer.

        Parameters
        ----------
        host_file : ROOT.TFile
            The TFile that will hold the calib TTree
        name : str
            The name of this TTree

        Returns
        -------
        (calib_ttree, buffer) : tuple
            The TTree object and the buffer used to fill its TBranches
        """
        buf = root_util.TreeBuffer()
        buf.triggerNumber = root_util.int_value()
        buf.detector = root_util.int_value()
        buf.timestamp_seconds = root_util.int_value()
        buf.timestamp_nanoseconds = root_util.int_value()
        buf.nHit = root_util.int_value()
        buf.charge = root_util.float_value()
        buf.fQuad = root_util.float_value()
        buf.fMax = root_util.float_value()
        buf.fPSD_t1 = root_util.float_value()
        buf.fPSD_t2 = root_util.float_value()
        buf.f2inch_maxQ = root_util.float_value()

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

        Parameters
        ----------
        host_file : ROOT.TFile
            The TFile that will hold the reco TTree
        name : str
            The name of this TTree

        Returns
        -------
        (reco_ttree, buffer) : tuple
            The TTree object and the buffer used to fill its TBranches
        """
        buf = root_util.TreeBuffer()
        buf.triggerType = root_util.unsigned_int_value()
        buf.site = root_util.int_value()
        buf.energy = root_util.float_value()
        buf.x = root_util.float_value()
        buf.y = root_util.float_value()
        buf.z = root_util.float_value()

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

    @staticmethod
    def prep_truth(TTree, host_file):
        """Create the MC Truth TTree (named MCTruth) and fill buffer.

        Parameters
        ----------
        host_file : ROOT.TFile
            The TFile that will hold the MC Truth TTree

        Returns
        -------
        (mc_truth_ttree, buffer) : tuple
            The TTree object and the buffer used to fill its TBranches
        """
        buf = root_util.TreeBuffer()
        buf.truth_label = root_util.unsigned_int_value()
        host_file.cd()
        name = "MCTruth"
        long_name = "Monte Carlo Truth information for each entry"
        mc_truth = TTree(name, long_name)
        mc_truth.Branch("truth_label", buf.truth_label, "truth_label/i")
        return mc_truth, buf

    @staticmethod
    def prep_truth_lookup(TTree, host_file, event_types):
        """Create the MC Truth Lookup TTree (named MCTruthLookup) and fill buffer.

        Each TBranch has a name which is either an integer, in which
        case the value on that TBranch is an array of chars describing
        the event subtype represented by that integer, or the converse:
        a subtype name with an integer value. This way the expression
        ``MCTruthLookup->Show(0)`` will print out both directions of
        lookup.

        Parameters
        ----------
        host_file : ROOT.TFile
            The TFile that will hold the MC Truth Lookup TTree
        event_types : list of :py:class:`EventType`
            The list of EventType objects to add to the lookup table


        Returns
        -------
        (mc_truth_lookup ttree, buffer) : tuple
            The TTree object and the buffer used to fill its TBranches
        """
        labels_by_number = []
        numbers_by_label = []
        for event_type in event_types:
            event_labels = event_type.labels()
            for number, label in event_labels.items():
                if number is None or number < 0 or not isinstance(number, int):
                    raise InvalidLookupError(event_type.name, label, number)
                numbers_by_label.append((label, number))
                labels_by_number.append((number, label))
        numbers_by_label.sort()
        labels_by_number.sort()
        max_label_length = max(len(x[0]) for x in numbers_by_label)
        buf_size = max_label_length + 1

        buf = root_util.TreeBuffer()

        def new_singleton_array(value):
            """Return a simple singleton array with value of type
            char*.

            There's no root-util function for char arrays so I'm making my
            own here. Further, python's built-in array.arrays are super
            inconvenient for bytestrings/char arrays so I'm using
            numpy.array instead. The "S{}" typecode means null-terminated
            bytes array with max length of buf_size.
            """
            type_format = "S{}".format(buf_size)
            return np.array([value], type_format)

        # Create and initialize the TreeBuffer buffers to the only
        # values they'll ever take
        for label, number in numbers_by_label:
            setattr(buf, label, root_util.unsigned_int_value())
            root_util.assign_value(getattr(buf, label), number)
        for number, label in labels_by_number:
            setattr(buf, "_{}".format(number), new_singleton_array(label))

        host_file.cd()
        name = "MCTruthLookup"
        long_name = "Monte Carlo Truth lookup table"
        mc_truth = TTree(name, long_name)
        for label, number in numbers_by_label:
            mc_truth.Branch(label, getattr(buf, label), "{}/i".format(label))
        for number, label in labels_by_number:
            name = "_{}".format(number)
            mc_truth.Branch(name, getattr(buf, name), "{}[{}]/C".format(name, buf_size))
        mc_truth.Fill()
        return mc_truth, buf


class EventType(ABC):
    """The base class for different event types.

    When you want to create new event types with new behavior, your
    class should inherit from this one (:py:class:`toymc.EventType`)

    Parameters
    ----------
    name : str
        The human-readable name for this event type. For ease of use
        in MC truth label names, this name should be a valid Python
        variable name (only alphanumerics and underscore, not starting
        with a number).
    """

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def generate_events(self, rng, duration_s):
        """Generate a list of :py:class:`Event` objects for the given
        duration.

        This is an internal function and is not intended to be called
        by users of the Toy Monte Carlo.

        This method should be overridden by any subclasses. The
        overriding method should use the ``rng`` parameter for any
        randomness that is needed, and should generate events between
        ``t=0`` and ``t=duration_s`` (**in seconds**). The events do not
        need to be sorted or in any particular order. Note that this
        method does not specify the *number* of events to generate. That
        is assumed to be a potentially configurable value or one that
        may be determined with some randomness.

        Parameters
        -----------
        rng : numpy.random.Generator
            The random number generator (RNG) that should be the sole
            source of randomness in the generated events
        duration_s : number
            The length of simulated DAQ time that the events should be
            generated within, **in seconds**

        Returns
        -------
        list of :py:class:`Event`
            The generated events
        """
        return []

    @abstractmethod
    def labels(self):
        """Return a dict containing the truth labels for this event
        type.

        The keys are the positive integer labels, and the values are
        the text labels corresponding to the integer keys.
        The text labels should be kept short (less
        than 20 characters) and should ideally be valid Python variable
        names to facilitate use as a TBranch in PyROOT. This means they
        should only consist of letters, numbers, and underscores, and
        should not start with a number.

        Returns
        -------
        labels : dict
            The dict mapping bytes labels to integer values as described
            above.
        """
        return {}

    @staticmethod
    def actual_event_count(rng, duration_s, rate_hz):
        """Generate an actual event count given the rate and duration.

        This is a helper method that simply multiplies the duration
        by the rate to get the total number of events. Note that for
        correlated events, this is more accurately the number of event
        "groups" rather than the number of sub-events.

        You can override this method for a particular subclass if you
        want different behavior.

        Parameters
        ----------
        rng : numpy.random.Generator
            The random number generator to use. Note: this is not used
            in the parent class implementation but you can use it in a
            subclass if you want.
        duration_s : number
            The length of time the DAQ is being run, **in seconds**
        rate_hz : number
            The event rate, **in hertz**

        Returns
        -------
        number
            The actual count of events to use
        """
        expected_count = duration_s * rate_hz
        return expected_count


Event = namedtuple(
    "Event",
    [
        "truth_index",
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

Event.__doc__ += """
The internal representation of a single triggered event.

This class is a ``namedtuple`` type which means it is immutable and has
convenient data access by name/attribute rather than by index. However,
when constructing a new :py:class:`Event` object, you must provide
**all** of the arguments **in the right order**. The order is shown in
the call signature above. Each field's documentation also includes the
(0-based) index corresponding to the correct order.
"""
Event.truth_index.__doc__ += """

The MC Truth index identifying the type of event. The index for each
event is stored in a special TTree whose entries line up with the data
TTrees. The lookup/meaning for each index is stored in its own special
TTree.
"""
Event.trigger_number.__doc__ += """

The trigger number for the event, inserted into the ``triggerNumber``
TBranch.
"""
Event.timestamp.__doc__ += """

The event timestamp, as an integer **in nanoseconds**.

In Python 3, integers have no upper bound so using an integer
number of nanoseconds is an ideal way to handle timestamps. The Toy
Monte Carlo will automatically break down this timestamp into the
``context.mTimeStamp.mSec`` and ``context.mTimeStamp.mNanoSec``
TBranches.
"""
Event.detector.__doc__ += """

The event detector (AD), i.e. 1, 2, 3, or 4. Will be inserted into the
``context.mDetId`` TBranch.
"""
Event.trigger_type.__doc__ += """

The event trigger type. Most regular events have a trigger type of
``0x10001100``, which means ESUM and NHIT. Will be inserted into the
``triggerType`` TBranch.
"""
Event.site.__doc__ += """

The event site (EH), i.e. 1, 2, or 4 (for EH3). Will be inserted into
the ``context.mSite`` TBranch.
"""
Event.energy.__doc__ += """

The event energy, in MeV. Will be inserted into the ``energy`` TBranch.
"""
Event.nHit.__doc__ += """

The event nHit value, i.e. number of hit PMTs. Will be inserted into the
``nHit`` TBranch.
"""
Event.charge.__doc__ += """

The event charge value (number of PEs). Will be inserted into the
``NominalCharge`` TBranch.
"""
Event.x.__doc__ += """

The event x position, **in millimeters**. Will be inserted into the
``x`` TBranch.
"""
Event.y.__doc__ += """

The event y position, **in millimeters**. Will be inserted into the
``y`` TBranch.
"""
Event.z.__doc__ += """

The event z position, **in millimeters**. Will be inserted into the
``z`` TBranch.
"""
Event.fMax.__doc__ += """

The maximum charge in any given PMT for the event. Will be inserted into
the ``MaxQ`` TBranch.
"""
Event.fQuad.__doc__ += """

The quadrant value for the event. Will be inserted into the ``Quadrant``
TBranch.
"""
Event.fPSD_t1.__doc__ += """

The first PSD discriminant for the event. Will be inserted into the
``time_PSD`` TBranch.
"""
Event.fPSD_t2.__doc__ += """

The second PSD discriminant for the event. Will be inserted into the
``time_PSD1`` TBranch.
"""
Event.f2inch_maxQ.__doc__ += """

The 2-inch PMT maximum charge value for the event. Will be inserted into
the ``MaxQ_2inchPMT`` TBranch.
"""


class InvalidLookupError(Exception):
    """Raised when an invalid subevent lookup number is encountered.

    Attributes
    ----------
    obj_name : str
        The name of the EventType object that this label was a part of
    label_name : str
        The subevent label that should have been numbered
    supplied_number : str
        The invalid supplied lookup number
    """

    def __init__(self, obj_name, label_name, supplied_number):
        self.obj_name = obj_name
        self.label_name = label_name
        self.supplied_number = supplied_number
        super().__init__(repr(self))

    def __repr__(self):
        return "{}(obj_name={}, label_name={}, supplied_number={})".format(
            self.__class__.__qualname__,
            repr(self.obj_name),
            repr(self.label_name),
            repr(self.supplied_number),
        )
