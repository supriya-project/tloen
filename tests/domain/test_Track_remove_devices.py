import asyncio

import pytest
from supriya.synthdefs import SynthDefFactory

from tloen.domain import Application, AudioEffect


@pytest.fixture
def synthdef_factory():
    return (
        SynthDefFactory()
        .with_channel_count(2)
        .with_input()
        .with_signal_block(lambda builder, source, state: (source * -2) + 0.25)
        .with_gate(0.01, 0.01)
        .with_output(replacing=True)
    )


@pytest.mark.asyncio
async def test_1(synthdef_factory):
    """
    Remove one device
    """
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    device = await track.add_device(AudioEffect, synthdef=synthdef_factory)
    await track.remove_devices(device)
    assert list(track.devices) == []
    assert device.application is None
    assert device.graph_order == ()
    assert device.parent is None
    assert device.provider is None


@pytest.mark.asyncio
async def test_2(synthdef_factory):
    """
    Remove two devices
    """
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    device_one = await track.add_device(AudioEffect, synthdef=synthdef_factory)
    device_two = await track.add_device(AudioEffect, synthdef=synthdef_factory)
    await track.remove_devices(device_one, device_two)
    assert list(track.devices) == []
    assert device_one.application is None
    assert device_one.graph_order == ()
    assert device_one.parent is None
    assert device_one.provider is None
    assert device_two.application is None
    assert device_two.graph_order == ()
    assert device_two.parent is None
    assert device_two.provider is None


@pytest.mark.asyncio
async def test_3(synthdef_factory):
    """
    Remove first device, leaving second untouched
    """
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    device_one = await track.add_device(AudioEffect, synthdef=synthdef_factory)
    device_two = await track.add_device(AudioEffect, synthdef=synthdef_factory)
    await track.remove_devices(device_one)
    assert list(track.devices) == [device_two]
    assert device_one.application is None
    assert device_one.graph_order == ()
    assert device_one.parent is None
    assert device_one.provider is None
    assert device_two.application is context.application
    assert device_two.graph_order == (2, 0, 0, 0, 6, 0)
    assert device_two.parent is track.devices
    assert device_two.provider is None


@pytest.mark.asyncio
async def test_4(synthdef_factory):
    """
    Boot, remove first device, leaving second untouched
    """
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    device_one = await track.add_device(AudioEffect, synthdef=synthdef_factory)
    device_two = await track.add_device(AudioEffect, synthdef=synthdef_factory)
    await application.boot()
    with context.provider.server.osc_protocol.capture() as transcript:
        await track.remove_devices(device_one)
    await asyncio.sleep(0.1)
    assert list(track.devices) == [device_two]
    assert device_one.application is None
    assert device_one.graph_order == ()
    assert device_one.parent is None
    assert device_one.provider is None
    assert device_two.application is context.application
    assert device_two.graph_order == (2, 0, 0, 0, 6, 0)
    assert device_two.parent is track.devices
    assert device_two.provider is context.provider
    assert len(transcript.sent_messages) == 1
    _, message = transcript.sent_messages[0]
    assert message.to_list() == [None, [["/n_set", 1014, "gate", 0]]]
    assert track.peak_levels == dict(
        input=(0.0, 0.0), postfader=(0.25, 0.25), prefader=(0.25, 0.25)
    )
    assert context.master_track.peak_levels == dict(
        input=(0.25, 0.25), postfader=(0.25, 0.25), prefader=(0.25, 0.25)
    )
