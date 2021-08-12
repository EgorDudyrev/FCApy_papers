from fcapy.poset import POSet, UpperSemiLattice, BinaryTree
from fcapy.context import FormalContext
from fcapy.lattice.formal_concept import FormalConcept
from fcapy.lattice import ConceptLattice
from copy import deepcopy


def compare_set_function(a, b):
    return set(b) & set(a) == set(b)


def compare_premise_function(a, b):
    return compare_set_function(a.premise, b.premise)


class ClassificationRule:
    def __init__(self, premise, target):
        self._premise = premise
        self._target = target

    @property
    def premise(self):
        return self._premise

    @property
    def target(self):
        return self._target

    def __repr__(self):
        return self.to_str(show_class_name=True)

    def to_str(self, show_class_name=True):
        class_name = self.__class__.__name__ if show_class_name else ''
        return f"{class_name}({self.premise},{self.target})"

    def __eq__(self, other):
        return self.premise == other.premise and self.target == other.target

    def __hash__(self):
        return hash((self._premise, self._target))


class DecisionPOSet(POSet):
    def __init__(self, classification_rules=None, premises=None, targets=None,
                 use_cache: bool = True, leq_premise_func=None, direct_subelements_dict=None):
        if classification_rules is not None:
            premises = [crule.premise for crule in classification_rules]
            targets = [crule.target for crule in classification_rules]
        elif premises is None or targets is None:
            raise ValueError(
                'Either `classification_rules` or a pair of (`premises`, `targets`) should be passed to DecisionPOSet')

        if not isinstance(premises, POSet):
            premises = POSet(
                elements=premises, leq_func=leq_premise_func,
                use_cache=use_cache, direct_subelements_dict=direct_subelements_dict
            )

        assert len(set(premises)) == len(premises), 'All premises should be unique'

        self._premises = premises
        self._targets = targets

        self._elements_to_index_map = {p: p_i for p_i, p in enumerate(premises)}
        self._use_cache = use_cache


    @property
    def premises(self):
        return self._premises

    @property
    def targets(self):
        return self._targets

    @property
    def elements(self):
        return self.classification_rules

    @property
    def classification_rules(self):
        return [ClassificationRule(p, t) for p, t in zip(self.premises, self.targets)]

    def index(self, element):
        p_i = self.premises.index(element.premise)
        if self._targets[p_i] == element.target:
            return p_i
        else:
            return None

    def leq_elements(self, a_index: int, b_index: int):
        return self.premises.leq_elements(a_index, b_index)

    def __repr__(self):
        k = 5
        is_big = len(self) > k
        elements_list = ', '.join([crule.to_str(False) for crule in self[:k]]) + (',...' if is_big else '')
        return f"{self.__class__.__name__}({len(self)} classification rules): [{elements_list}]"

    def __and__(self, other):
        raise NotImplementedError

    def __or__(self, other):
        raise NotImplementedError

    def __xor__(self, other):
        raise NotImplementedError

    def __sub__(self, other):
        raise NotImplementedError

    def __len__(self):
        return len(self.premises)

    def __delitem__(self, key):
        #raise NotImplementedError
        del self._premises[key]
        del self._targets[key]
        self._elements_to_index_map = {p: p_i for p_i, p in enumerate(self.premises)}
        

    def add(self, element, fill_up_cache=True):
        #raise NotImplementedError
        self._premises.add(element.premise)
        self._targets.append(element.target)
        self._elements_to_index_map = {p: p_i for p_i, p in enumerate(self.premises)}

    def __eq__(self, other):
        raise NotImplementedError

    def trace_element(self, element, direction: str):
        raise NotImplementedError
    
    def super_elements(self, element_index: int):
        """Return a set of indexes of elements of POSet bigger than element #``element_index``"""
        return self.premises.super_elements(element_index)
    
    def sub_elements(self, element_index: int):
        """Return a set of indexes of elements of POSet smaller than element #``element_index``"""
        return self.premises.sub_elements(element_index)
    
    def direct_super_elements(self, element_index: int):
        return self.premises.direct_super_elements(element_index)
    
    def direct_sub_elements(self, element_index: int):
        return self.premises.direct_sub_elements(element_index)
    
    @property
    def top_elements(self):
        """A list of the top (the biggest) elements in a DecisionTree"""
        return self.premises.top_elements


class DecisionTree(DecisionPOSet, BinaryTree):
    pass


def concept_lattice_from_decision_tree(context: FormalContext, dt: DecisionTree):
    """Convert DecisionTree objects to ConceptLattice

    Parameters
    ----------
    context: `FormalContext`
        A context to create ConceptLattice.
    dt: `DecisionTree`
        A DecisionTree model
    Returns
    -------
    concepts: `list` of `PatternConcept`
        A list of PatternConcepts retrieved from context by DecisionTree

    """
    premises = deepcopy(dt.premises)
    premises.add(context.attribute_names)
    
    extents = [context.extension(p) for p in premises]
    intents = [context.intention(ext_) for ext_ in extents]
    
    extents_i = [tuple([context.object_names.index(g) for g in ext_]) for ext_ in extents]
    intents_i = [tuple([context.attribute_names.index(m) for m in int_]) for int_ in intents]
    
    context_hash = context.hash_fixed()    
    concepts = [FormalConcept(extents_i[c_i], extents[c_i], intents_i[c_i], intents[c_i], context_hash=context_hash)
                for c_i in range(len(premises))]


    sbc_dict = deepcopy(dt.premises.direct_sub_elements_dict)
    bc_i = len(concepts)-1
    for el_i in dt.premises.bottom_elements:
        sbc_dict[el_i] = {bc_i}
    L = ConceptLattice(concepts, subconcepts_dict=sbc_dict)
    
    return L
