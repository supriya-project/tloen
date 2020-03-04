import pytest

from tloen.domain import Application, Instrument, RackDevice, Transfer
from tloen.midi import NoteOnMessage


@pytest.mark.asyncio
async def test():
    application = await (await Application.new(1, 1, 1)).boot()
    track = application.contexts[0].tracks[0]
    rack = await track.add_device(RackDevice)
    chain_one = await rack.add_chain(
        name="One", transfer=Transfer(in_pitch=60, out_pitch=60),
    )
    chain_two = await rack.add_chain(
        name="Two", transfer=Transfer(in_pitch=61, out_pitch=60),
    )
    one = await chain_one.add_device(Instrument)
    two = await chain_two.add_device(Instrument)
    with one.capture() as transcript_one, two.capture() as transcript_two:
        await track.perform([NoteOnMessage(pitch=60, velocity=100)])
    assert list(transcript_one) == [
        one.CaptureEntry(
            moment=None, label="I", message=NoteOnMessage(pitch=60, velocity=100)
        )
    ]
    assert list(transcript_two) == []
    with one.capture() as transcript_one, two.capture() as transcript_two:
        await track.perform([NoteOnMessage(pitch=61, velocity=100)])
    assert list(transcript_one) == []
    assert list(transcript_two) == [
        one.CaptureEntry(
            moment=None, label="I", message=NoteOnMessage(pitch=60, velocity=100)
        )
    ]
