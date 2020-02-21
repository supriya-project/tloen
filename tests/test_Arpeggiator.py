import logging
import asyncio

import pytest
from supriya.assets.synthdefs import default

from tloen.core import Application, Arpeggiator, Instrument
from tloen.core.midi import NoteOffMessage, NoteOnMessage


@pytest.fixture(autouse=True)
def logger(caplog):
    caplog.set_level(logging.DEBUG, logger="tloen.core")
    caplog.set_level(logging.DEBUG, logger="supriya.clock")


@pytest.fixture
async def application():
    application = Application()
    context = await application.add_context(name="Context")
    await context.add_track(name="Track")
    await application.boot()
    default.allocate(server=context.provider.server)
    yield application
    await application.quit()


@pytest.mark.timeout(3)
@pytest.mark.asyncio
async def test_timeout(application):
    application["Track"].add_device(Arpeggiator)
    application["Track"].add_device(Instrument, synthdef=default)
    await asyncio.sleep(0.1)
    application.transport.perform([NoteOnMessage(pitch=60, velocity=100)])
    await asyncio.sleep(1.0)


@pytest.mark.asyncio
async def test_query_1(application):
    """
    Arpeggiator does not modify the server node tree.
    """
    before = str(await application["Track"].query())
    await application["Track"].add_device(Arpeggiator)
    await asyncio.sleep(0.1)
    after = str(await application["Track"].query())
    assert before == after


@pytest.mark.asyncio
async def test_osc_transcript(application):
    """
    Arpeggiator instantiation does not send any OSC messages.
    """
    with application["Context"].provider.server.osc_protocol.capture() as transcript:
        await application["Track"].add_device(Arpeggiator)
    assert len(transcript.sent_messages) == 0


@pytest.mark.asyncio
async def test_midi_transcript_1(mocker, application):
    time_mock = mocker.patch.object(application.transport._clock, "get_current_time")
    time_mock.return_value = 0.0
    arpeggiator = await application["Track"].add_device(Arpeggiator)
    assert not application.transport.is_running
    with arpeggiator.capture() as transcript:
        application.transport.perform([NoteOnMessage(pitch=60, velocity=100)])
        assert application.transport.is_running
        await asyncio.sleep(0.1)
        time_mock.return_value = 0.5
        await asyncio.sleep(0.1)
    assert [(_.label, _.moment.offset, _.message) for _ in transcript] == [
        ("I", 0.0, NoteOnMessage(pitch=60, velocity=100)),
        ("O", 0.0, NoteOnMessage(pitch=60, velocity=100)),
        ("O", 0.0625, NoteOffMessage(pitch=60)),
        ("O", 0.0625, NoteOnMessage(pitch=60, velocity=100)),
        ("O", 0.125, NoteOffMessage(pitch=60)),
        ("O", 0.125, NoteOnMessage(pitch=60, velocity=100)),
        ("O", 0.1875, NoteOffMessage(pitch=60)),
        ("O", 0.1875, NoteOnMessage(pitch=60, velocity=100)),
        ("O", 0.25, NoteOffMessage(pitch=60)),
        ("O", 0.25, NoteOnMessage(pitch=60, velocity=100)),
    ]


@pytest.mark.asyncio
async def test_midi_transcript_2(mocker, application):
    time_mock = mocker.patch.object(application.transport._clock, "get_current_time")
    time_mock.return_value = 0.0
    arpeggiator = await application["Track"].add_device(Arpeggiator)
    assert not application.transport.is_running
    with arpeggiator.capture() as transcript:
        application.transport.perform([NoteOnMessage(pitch=60, velocity=100)])
        application.transport.perform([NoteOnMessage(pitch=63, velocity=100)])
        application.transport.perform([NoteOnMessage(pitch=67, velocity=100)])
        assert application.transport.is_running
        await asyncio.sleep(0.1)
        time_mock.return_value = 0.5
        await asyncio.sleep(0.1)
    assert [(_.label, _.moment.offset, _.message) for _ in transcript] == [
        ("I", 0.0, NoteOnMessage(pitch=60, velocity=100)),
        ("I", 0.0, NoteOnMessage(pitch=63, velocity=100)),
        ("I", 0.0, NoteOnMessage(pitch=67, velocity=100)),
        ("O", 0.0, NoteOnMessage(pitch=60, velocity=100)),
        ("O", 0.0625, NoteOffMessage(pitch=60)),
        ("O", 0.0625, NoteOnMessage(pitch=63, velocity=100)),
        ("O", 0.125, NoteOffMessage(pitch=63)),
        ("O", 0.125, NoteOnMessage(pitch=67, velocity=100)),
        ("O", 0.1875, NoteOffMessage(pitch=67)),
        ("O", 0.1875, NoteOnMessage(pitch=60, velocity=100)),
        ("O", 0.25, NoteOffMessage(pitch=60)),
        ("O", 0.25, NoteOnMessage(pitch=63, velocity=100)),
    ]
