import asyncio

import pytest
from supriya.assets.synthdefs import default
from uqbar.strings import normalize

from tloen.domain import Application, Instrument
from tloen.domain.midi import NoteOnMessage


@pytest.fixture
async def application():
    application = Application()
    context = await application.add_context(name="Context")
    await context.add_track(name="Track")
    await application.boot()
    yield application
    await application.quit()


@pytest.mark.asyncio
async def test_1(application):
    await application.boot()
    track = application.primary_context["Track"]
    instrument = await track.add_device(Instrument, synthdef=default)
    await asyncio.sleep(0.01)
    async with instrument.lock(instrument, 0.0):
        with instrument.capture() as transcript:
            await instrument.perform([NoteOnMessage(pitch=57, velocity=100)])
    await asyncio.sleep(0.01)
    assert list(transcript) == [
        instrument.CaptureEntry(
            moment=None, label="I", message=NoteOnMessage(pitch=57, velocity=100)
        )
    ]
    assert str(await instrument.query()) == normalize(
        """
        NODE TREE 1044 group (Instrument)
            1047 mixer/patch[replace]/2x2 (DeviceIn)
                active: 1.0, gate: 1.0, in_: 18.0, lag: 0.01, out: 28.0
            1045 group (Parameters)
            1046 group (Body)
                1049 default
                    out: 28.0, amplitude: 0.620001, frequency: 220.0, gate: 1.0, pan: 0.5
            1048 mixer/patch[hard,mix]/2x2 (DeviceOut)
                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 28.0, lag: 0.01, mix: 1.0, out: 18.0
        """
    )
    async with instrument.lock(instrument, 0.0):
        with instrument.capture() as transcript:
            await instrument.perform([NoteOnMessage(pitch=57, velocity=127)])
    await asyncio.sleep(0.01)
    assert list(transcript) == [
        instrument.CaptureEntry(
            moment=None, label="I", message=NoteOnMessage(pitch=57, velocity=127)
        )
    ]
    assert str(await instrument.query()) == normalize(
        """
        NODE TREE 1044 group (Instrument)
            1047 mixer/patch[replace]/2x2 (DeviceIn)
                active: 1.0, gate: 1.0, in_: 18.0, lag: 0.01, out: 28.0
            1045 group (Parameters)
            1046 group (Body)
                1050 default
                    out: 28.0, amplitude: 1.0, frequency: 220.0, gate: 1.0, pan: 0.5
                1049 default
                    out: 28.0, amplitude: 0.620001, frequency: 220.0, gate: 0.0, pan: 0.5
            1048 mixer/patch[hard,mix]/2x2 (DeviceOut)
                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 28.0, lag: 0.01, mix: 1.0, out: 18.0
        """
    )
