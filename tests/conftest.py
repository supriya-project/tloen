import pytest
from supriya.enums import DoneAction
from supriya.synthdefs import SynthDefFactory
from supriya.ugens import DC, Linen

from tloen.core import Application, AudioEffect, RackDevice


"""
@pytest.fixture(autouse=True)
def logger(caplog):
    import logging

    caplog.set_level(logging.DEBUG, logger="supriya.osc")
    caplog.set_level(logging.DEBUG, logger="supriya.server")
"""


@pytest.fixture
def dc_index_synthdef_factory():
    def signal_block(builder, source, state):
        return DC.ar(1) * builder["index"].is_equal_to(range(state["channel_count"]))

    return (
        SynthDefFactory(index=0)
        .with_channel_count(2)
        .with_signal_block(signal_block)
        .with_output()
    )


@pytest.fixture
def dc_instrument_synthdef_factory():
    def signal_block(builder, source, state):
        gate = Linen.kr(
            attack_time=builder["lag"],
            done_action=DoneAction.FREE_SYNTH,
            gate=builder["gate"],
            release_time=builder["lag"],
        )
        return (
            DC.ar(builder["value"])
            * gate
            * builder["index"].is_equal_to(range(state["channel_count"]))
        )

    return (
        SynthDefFactory(value=1, gate=1, lag=0.01, index=0)
        .with_channel_count(2)
        .with_signal_block(signal_block)
        .with_output()
    )


@pytest.fixture
async def track_mute_solo_application(dc_index_synthdef_factory):
    application = Application(channel_count=8)
    context = await application.add_context()
    track_a = await context.add_track(name="a")
    track_b = await context.add_track(name="b")
    track_c = await context.add_track(name="c")
    track_ba = await track_b.add_track(name="ba")
    track_bb = await track_b.add_track(name="bb")
    track_ca = await track_c.add_track(name="ca")
    track_cb = await track_c.add_track(name="cb")
    track_cba = await track_cb.add_track(name="cba")
    for i, track in enumerate(
        [track_a, track_b, track_ba, track_bb, track_c, track_ca, track_cb, track_cba]
    ):
        await track.add_device(
            AudioEffect,
            synthdef=dc_index_synthdef_factory,
            synthdef_kwargs=dict(index=i),
        )
    yield application
    await application.quit()


@pytest.fixture
async def chain_mute_solo_application(dc_index_synthdef_factory):
    application = Application(channel_count=8)
    context = await application.add_context()
    track = await context.add_track()
    rack_outer_a = await track.add_device(RackDevice, name="outer/a")
    chain_outer_a_a = await rack_outer_a.add_chain(name="outer/a/a")
    chain_outer_a_b = await rack_outer_a.add_chain(name="outer/a/b")
    rack_inner_a = await chain_outer_a_b.add_device(RackDevice, name="inner/a")
    chain_inner_a_a = await rack_inner_a.add_chain(name="inner/a/a")
    chain_inner_a_b = await rack_inner_a.add_chain(name="inner/a/b")
    rack_outer_b = await track.add_device(RackDevice, name="outer/b")
    chain_outer_b_a = await rack_outer_b.add_chain(name="outer/b/a")
    chain_outer_b_b = await rack_outer_b.add_chain(name="outer/b/b")
    rack_inner_b = await chain_outer_b_b.add_device(RackDevice, name="inner/b")
    chain_inner_b_a = await rack_inner_b.add_chain(name="inner/b/a")
    chain_inner_b_b = await rack_inner_b.add_chain(name="inner/b/b")
    for i, chain in enumerate(
        [
            chain_outer_a_a,
            chain_outer_a_b,
            chain_inner_a_a,
            chain_inner_a_b,
            chain_outer_b_a,
            chain_outer_b_b,
            chain_inner_b_a,
            chain_inner_b_b,
        ]
    ):
        await chain.add_device(
            AudioEffect,
            synthdef=dc_index_synthdef_factory,
            synthdef_kwargs=dict(index=i),
        )
    return application


@pytest.fixture
async def channel_count_application(dc_index_synthdef_factory):
    application = Application(channel_count=2)
    context = await application.add_context(name="Context")
    track_one = await context.add_track(name="One")
    track_two = await context.add_track(name="Two")
    await track_two.add_track(name="Three")
    rack = await track_one.add_device(RackDevice, name="Rack")
    chain = await rack.add_chain(name="Chain")
    await chain.add_device(
        AudioEffect,
        name="Device",
        synthdef=dc_index_synthdef_factory,
        synthdef_kwargs=dict(index=0),
    )
    return application
