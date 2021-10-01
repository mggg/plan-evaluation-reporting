from gerrychain import Partition, MarkovChain, constraints, accept
from gerrychain.updaters import Tally
from gerrychain.tree import recursive_tree_part
from gerrychain.proposals import ReCom
from pcompress import Record
from functools import partial
import warnings
from region_aware import *

class ChainRecorder:
    def __init__(self, graph, output_dir, pop_col, county_col=None, verbose_freq=None) -> None:
        self.graph = graph
        self.output_dir = output_dir
        self.pop_col = pop_col
        self.county_col = county_col
        self.verbose_freq = verbose_freq

        ## Set up pop info
        self.tot_pop = sum([graph.nodes()[n][pop_col] for n in graph.nodes()])
        self.updaters = {"population": Tally(pop_col, alias="population")}


    def _initial_partition(self, num_districts, epsilon):
        ideal_pop = self.tot_pop / num_districts
        cddict = recursive_tree_part(self.graph, range(num_districts), ideal_pop, self.pop_col,
                                     epsilon)
        part = Partition(self.graph, assignment=cddict, updaters=self.updaters)
        return part

    def _proposal(self, num_districts, epsilon, county_aware):
        ideal_pop = self.tot_pop / num_districts

        if county_aware and self.county_col is None:
            warnings.warn("County column needs to be specified to run county aware chains.  Defaulting\
                          to running neutral chain with other settings.")

        if county_aware and self.county_col is not None:
            return ReCom(self.pop_col, ideal_pop, epsilon,
                         method=partial(division_bipartition_tree, division_tuples=[(self.county_col, 1)],
                                        first_check_division=True))
        else:
            return ReCom(self.pop_col, ideal_pop, epsilon)

    def record_chain(self, num_districts, epsilon, steps, file_name, county_aware=False,
                     initial_partition=None):
        if initial_partition is None:
            initial_partition = self._initial_partition(num_districts, epsilon)

        proposal = self._proposal(num_districts, epsilon, county_aware)
        cs = [constraints.within_percent_of_ideal_population(initial_partition, epsilon)]
        accept_func = accept.always_accept

        chain = MarkovChain(proposal=proposal, constraints=cs,
                            accept=accept_func, initial_state=initial_partition,
                            total_steps=steps)

        for i, part in  enumerate(Record(chain, "{}/{}".format(self.output_dir, file_name))):
            if self.verbose_freq is not None and i % self.verbose_freq == self.verbose_freq - 1:
                print("*", end="")
