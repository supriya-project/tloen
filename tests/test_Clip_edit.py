import asyncio
import logging

import pytest
from supriya.clock import AsyncTempoClock, Moment

from tloen.domain import Application, Instrument, Note
from tloen.midi import NoteOffMessage, NoteOnMessage

logger = logging.getLogger("tloen.test")


@pytest.fixture(autouse=True)
def capture_logs(caplog):
    caplog.set_level(logging.DEBUG, logger="supriya.clock")
    caplog.set_level(logging.DEBUG, logger="tloen")


@pytest.fixture
async def application(mocker, monkeypatch):
    async def wait_for_event(self, sleep_time):
        await asyncio.sleep(0)
        await self._event.wait()
        logger.info("Waking up")

    monkeypatch.setattr(AsyncTempoClock, "_wait_for_event", wait_for_event)
    mock_time = mocker.patch.object(AsyncTempoClock, "get_current_time")
    mock_time.return_value = 0.0

    application = await Application.new(1, 2, 2)
    await application.boot()
    track = application.contexts[0].tracks[0]
    await track.add_device(Instrument)
    await track.slots[0].add_clip()
    yield application
    await application.quit()


async def set_time(new_time, transport):
    logger.info(f"Setting transport time to {new_time}")
    transport._clock.get_current_time.return_value = new_time
    transport._clock._event.set()
    await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_1(mocker, application):
    """
    Delete a note.
    """
    track = application.contexts[0].tracks[0]
    await track.slots[0].clip.add_notes([Note(0, 1, pitch=60)])
    with track.devices[0].capture() as transcript:
        await track.slots[0].fire()
        await set_time(0, application.transport)
    assert track.slots[0].clip.is_playing
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
        await set_time(0.5, application.transport)
    assert list(transcript) == []
    with track.devices[0].capture() as transcript:
        await track.slots[0].clip.remove_notes(track.slots[0].clip.notes)
        await asyncio.sleep(0)
    assert track.slots[0].clip.is_playing
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
    track = application.contexts[0].tracks[0]
    with track.devices[0].capture() as transcript:
        await track.slots[0].fire()
        await set_time(0, application.transport)
        assert list(transcript) == []
    with track.devices[0].capture() as transcript:
        await track.slots[0].clip.add_notes([Note(0.75, 1, pitch=60)])
        await set_time(0, application.transport)
        assert list(transcript) == []
    with track.devices[0].capture() as transcript:
        await set_time(2.0, application.transport)
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
