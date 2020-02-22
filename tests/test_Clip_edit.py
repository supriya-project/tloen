import asyncio
import logging

import pytest
from supriya.clock import Moment

from tloen.domain import Application, Instrument, Note
from tloen.domain.midi import NoteOffMessage, NoteOnMessage


@pytest.fixture(autouse=True)
def logger(caplog):
    caplog.set_level(logging.DEBUG, logger="supriya.clock")
    caplog.set_level(logging.DEBUG, logger="tloen.domain")


@pytest.fixture
async def application():
    application = await Application.new(1, 1, 1)
    await application.boot()
    track = application.contexts[0].tracks[0]
    await track.add_device(Instrument)
    await track.slots[0].add_clip()
    yield application
    await application.quit()


@pytest.mark.asyncio
async def test_1(mocker, application):
    """
    Delete a note.
    """
    time_mock = mocker.patch.object(application.transport._clock, "get_current_time")
    time_mock.return_value = 0.0
    track = application.contexts[0].tracks[0]
    track.slots[0].clip.add_notes([Note(0, 1, pitch=60)])
    with track.devices[0].capture() as transcript:
        await track.slots[0].fire()
        await asyncio.sleep(0.01)
    assert list(transcript) == [
        Instrument.CaptureEntry(
            moment=Moment(
                beats_per_minute=120.0,
                measure=1,
                measure_offset=0.0,
                offset=0.0,
                seconds=0.0,
                time_signature=(4, 4),
            ),
            label="I",
            message=NoteOnMessage(pitch=60, velocity=100.0),
        )
    ]
    with track.devices[0].capture() as transcript:
        time_mock.return_value = 0.5
        await asyncio.sleep(0.01)
    assert list(transcript) == []
    with track.devices[0].capture() as transcript:
        track.slots[0].clip.remove_notes(track.slots[0].clip.notes)
        await asyncio.sleep(0.1)
    assert list(transcript) == [
        Instrument.CaptureEntry(
            moment=Moment(
                beats_per_minute=120.0,
                measure=1,
                measure_offset=0.25,
                offset=0.25,
                seconds=0.5,
                time_signature=(4, 4),
            ),
            label="I",
            message=NoteOffMessage(pitch=60),
        )
    ]


@pytest.mark.asyncio
async def test_2(mocker, application):
    """
    Add a note.
    """
    time_mock = mocker.patch.object(application.transport._clock, "get_current_time")
    time_mock.return_value = 0.0
    track = application.contexts[0].tracks[0]
    with track.devices[0].capture() as transcript:
        await track.slots[0].fire()
        await asyncio.sleep(0.01)
        assert list(transcript) == []
    with track.devices[0].capture() as transcript:
        track.slots[0].clip.add_notes([Note(0.75, 1, pitch=60)])
        await asyncio.sleep(0.01)
        assert list(transcript) == []
    with track.devices[0].capture() as transcript:
        time_mock.return_value = 2.0
        await asyncio.sleep(0.01)
        assert list(transcript) == [
            Instrument.CaptureEntry(
                moment=Moment(
                    beats_per_minute=120.0,
                    measure=1,
                    measure_offset=0.75,
                    offset=0.75,
                    seconds=1.5,
                    time_signature=(4, 4),
                ),
                label="I",
                message=NoteOnMessage(pitch=60, velocity=100.0),
            ),
            Instrument.CaptureEntry(
                moment=Moment(
                    beats_per_minute=120.0,
                    measure=2,
                    measure_offset=0.0,
                    offset=1.0,
                    seconds=2.0,
                    time_signature=(4, 4),
                ),
                label="I",
                message=NoteOffMessage(pitch=60, velocity=100.0),
            ),
        ]
