import asyncio
import logging

import pytest
from supriya.clocks import AsyncTempoClock, Moment

from tloen.domain import Application, Instrument, Note
from tloen.midi import NoteOffMessage, NoteOnMessage

logger = logging.getLogger("tloen.test")


@pytest.fixture(autouse=True)
def capture_logs(caplog):
    caplog.set_level(logging.DEBUG, logger="supriya.clocks")
    caplog.set_level(logging.DEBUG, logger="tloen")


@pytest.fixture
async def application(mocker, monkeypatch):
    async def wait_for_event(self, sleep_time):
        await asyncio.sleep(0)
        await self._event.wait()

    monkeypatch.setattr(AsyncTempoClock, "_wait_for_event", wait_for_event)
    mock_time = mocker.patch.object(AsyncTempoClock, "get_current_time")
    mock_time.return_value = 0.0

    application = await Application.new(1, 2, 2)
    await application.boot()
    track = application.contexts[0].tracks[0]
    await track.add_device(Instrument)
    await track.slots[0].add_clip(
        notes=[
            Note(0, 0.25, pitch=60),
            Note(0.25, 0.5, pitch=62),
            Note(0.5, 0.75, pitch=64),
            Note(0.75, 1.0, pitch=65),
        ]
    )
    yield application
    await application.quit()


async def set_time(new_time, transport):
    logger.info(f"Setting transport time to {new_time}")
    transport._clock.get_current_time.return_value = new_time
    transport._clock._event.set()
    await asyncio.sleep(0.01)


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_1(mocker, application):
    """
    Fire non-empty slot, then fire empty-slot
    """
    with application.contexts[0].tracks[0].devices[0].capture() as transcript:
        await application.contexts[0].tracks[0].slots[0].fire()
        assert application.transport.is_running
        await set_time(0, application.transport)
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
    with application.contexts[0].tracks[0].devices[0].capture() as transcript:
        await application.contexts[0].tracks[0].slots[1].fire()
        await asyncio.sleep(0)
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
            message=NoteOffMessage(pitch=60),
        )
    ]


@pytest.mark.asyncio
async def test_2(mocker, application):
    """
    Fire non-empty slot, then re-fire same slot
    """
    with application.contexts[0].tracks[0].devices[0].capture() as transcript:
        await application.contexts[0].tracks[0].slots[0].fire()
        assert application.transport.is_running
        await set_time(0, application.transport)
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
    with application.contexts[0].tracks[0].devices[0].capture() as transcript:
        await application.contexts[0].tracks[0].slots[0].fire()
        await asyncio.sleep(0)
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
            message=NoteOffMessage(pitch=60),
        ),
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
        ),
    ]
