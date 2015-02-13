# -*- coding: utf-8 -*-
"""Field selection via exclusion or inclusion policy

"""

from kids.cache import cache


@cache
def parse_field_specs(fields_cli, current_model=None):
    """Return internal spec from CLI string field spec

        >>> from pprint import pprint as pp

    Model attribution
    -----------------

    Syntaxes uses MODEL:FIELD[,FIELD]

        >>> pp(parse_field_specs('model:f1,f2', current_model='foo'))
        {'model': {'f1': True, 'f2': True}}

    But if you don't specify the model, it'll be the current_model::

        >>> pp(parse_field_specs('f1,f2', current_model='foo'))
        {'foo': {'f1': True, 'f2': True}}

    Chaining Model attribution
    --------------------------

    You can use the previous syntax several times separated with ';' to give
    multiple model attributions::

        >>> pp(parse_field_specs('model:f1;f3', current_model='foo'))
        {'foo': {'f3': True}, 'model': {'f1': True}}

    When '*' string is used as a model, this is for all the records. Rules
    will use this spec as a basis and then use any other specific specs as
    additional info::

        >>> pp(parse_field_specs('*:f1,f2', current_model='foo'))
        {'*': {'f1': True, 'f2': True}}

    Fields parsing and rules
    ------------------------

    Using '+' or not using anything is the same::

        >>> pp(parse_field_specs('foo:f1', 'bar'))
        {'foo': {'f1': True}}
        >>> pp(parse_field_specs('foo:+f1', 'bar'))
        {'foo': {'f1': True}}

    Using '-' will cast out this field. Here's how it'll be stored::

        >>> pp(parse_field_specs('foo:-f1', 'bar'))
        {'foo': {'f1': False}}

    Only the last value has prevalence::

        >>> pp(parse_field_specs('foo:f1,-f1,+f1', 'bar'))
        {'foo': {'f1': True}}
        >>> pp(parse_field_specs('foo:-f1,+f1', 'bar'))
        {'foo': {'f1': True}}
        >>> pp(parse_field_specs('foo:f1,+f1,-f1', 'bar'))
        {'foo': {'f1': False}}

    Multiple spec on the same model concats::

        >>> pp(parse_field_specs('foo:f1;foo:-f1', 'bar'))
        {'foo': {'f1': False}}
        >>> pp(parse_field_specs('foo:-f1;foo:+f1', 'bar'))
        {'foo': {'f1': True}}
        >>> pp(parse_field_specs('foo:f1;foo:+f1,-f1', 'bar'))
        {'foo': {'f1': False}}

    Empty string is empty spec::

        >>> pp(parse_field_specs('', 'bar'))
        {}

    """
    specs = {}
    for model_spec in fields_cli.split(";"):
        if not model_spec:
            continue
        if ":" not in model_spec:
            model = current_model
            fields_spec = model_spec
        else:
            model, fields_spec = model_spec.split(':')
        specs[model] = dict(
            (label[1:] if label[0] in "+-" else label,
             label[0] != "-")
            for label in fields_spec.split(",")
            if label)
    return specs


@cache
def is_field_selected(model, field, spec):
    """Apply field_specs to tell if model.field is to be included

        >>> specs = lambda s: parse_field_specs(s)

    Basic direct usage
    ------------------

    If explicitely selected::

        >>> is_field_selected('bar', 'f1', specs('bar:f1'))
        True

    Default is to select so::

        >>> is_field_selected('bar', 'f1', {})
        True

    And if explicitely unselected::

        >>> is_field_selected('bar', 'f1', specs('bar:-f1'))
        False

    Of course the spec must be targetting the correct model::

        >>> is_field_selected('bar', 'f1', specs('foo:-f1'))
        True

    Or the correct field::

        >>> is_field_selected('bar', 'f1', specs('bar:-f2'))
        True

    Wildcards
    ---------

    '*' on models should hit all models::

        >>> is_field_selected('bar', 'f1', specs('*:-f1'))
        False

    '*' on fields should hit all fields::

        >>> is_field_selected('bar', 'f1', specs('bar:-*'))
        False

    But wildcards have less priority than direct spec::

        >>> is_field_selected('bar', 'f1', specs('*:-f1;bar:f1'))
        True

        >>> is_field_selected('bar', 'f1', specs('*:-*;bar:f1'))
        True

        >>> is_field_selected('bar', 'f1', specs('bar:-*;bar:f1'))
        True

        >>> is_field_selected('bar', 'f1', specs('bar:-*;bar:-*,f1'))
        True

    """

    field_spec = spec.get('*', {}).copy()
    field_spec.update(spec.get(model, {}))

    default = field_spec.get('*', True)
    return field_spec.get(field, default)
