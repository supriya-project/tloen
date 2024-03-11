class SynthQueryRequest(Request):
    """
    A /s_query request.

    ::

        >>> import supriya.commands
        >>> request = supriya.commands.SynthQueryRequest(1000)
        >>> request
        SynthQueryRequest(
            node_ids=(1000,),
        )

    ::

        >>> request.to_osc()
        OscMessage('/s_query', 1000)

    ::

        >>> server = supriya.Server().boot()
        >>> synth = supriya.Synth().allocate(server)
        >>> request.communicate(server)
        SynthInfoResponse(
            1000,
            'default',
            amplitude=0.100...,
            frequency=440.0,
            gate=1.0,
            out=0.0,
            pan=0.5,
        )

    """

    ### CLASS VARIABLES ###

    request_id = RequestId.SYNTH_QUERY

    ### INITIALIZER ###

    def __init__(self, node_ids=None):
        Request.__init__(self)
        if not isinstance(node_ids, Sequence):
            node_ids = (node_ids,)
        node_ids = tuple(int(_) for _ in node_ids)
        self._node_ids = node_ids

    ### PUBLIC METHODS ###

    def to_osc(self, *, with_placeholders=False):
        contents = [self.request_name, *self.node_ids]
        message = supriya.osc.OscMessage(*contents)
        return message

    ### PUBLIC PROPERTIES ###

    @property
    def node_ids(self):
        return self._node_ids

    @property
    def response_patterns(self):
        return ["/s_info", int(self.node_ids[-1])], None


class SynthInfoResponse(Response):

    ### INITIALIZER ###

    def __init__(self, node_id, synthdef_name, **synthdef_controls):
        self.node_id = node_id
        self.synthdef_name = synthdef_name
        self.synthdef_controls = synthdef_controls

    @classmethod
    def from_osc_message(cls, osc_message):
        contents = list(osc_message.contents)
        node_id = contents.pop(0)
        synthdef_name = contents.pop(0)
        pair_count = contents.pop(0)
        kwargs = {}
        for i in range(pair_count):
            kwargs[contents[i * 2]] = contents[i * 2 + 1]
        return cls(node_id=node_id, synthdef_name=synthdef_name, **kwargs)


