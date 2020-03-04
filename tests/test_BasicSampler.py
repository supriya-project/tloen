import pytest
from supriya.synthdefs import SynthDefCompiler
from supriya.utils import locate

from tloen.domain import Application, BasicSampler, DeviceIn, DeviceOut
from tloen.midi import NoteOnMessage


@pytest.fixture
async def application():
    application = Application()
    context = await application.add_context(name="Context")
    await context.add_track(name="Track")
    await application.boot()
    yield application
    await application.quit()


@pytest.mark.asyncio
async def test_add(application):
    track = application.primary_context["Track"]
    with application.primary_context.capture() as transcript:
        _ = await track.add_device(BasicSampler)
    assert len(transcript.sent_messages) == 1
    _, message = transcript.sent_messages[0]
    compiled_synthdefs = bytearray(
        SynthDefCompiler.compile_synthdefs(
            [DeviceOut.build_synthdef(2, 2), DeviceIn.build_synthdef(2, 2)]
        )
    )
    bundle_contents = [
        ["/g_new", 1044, 1, 1013],
        ["/g_new", 1045, 0, 1044],
        ["/g_new", 1046, 1, 1044],
        ["/s_new", "mixer/patch[replace]/2x2", 1047, 0, 1044, "in_", 18.0, "out", 28.0],
        [
            "/s_new",
            "mixer/patch[hard,mix]/2x2",
            1048,
            1,
            1044,
            "in_",
            28.0,
            "out",
            18.0,
        ],
    ]
    assert message.to_list() == [
        None,
        [["/d_recv", compiled_synthdefs, [None, bundle_contents]]],
    ]


@pytest.mark.asyncio
async def test_set_buffer(application):
    track = application.primary_context["Track"]
    instrument = await track.add_device(BasicSampler)
    assert instrument.parameters["buffer_id"].buffer_proxy is None
    assert instrument.parameters["buffer_id"].path is None
    path = "tloen:samples/808/bd-long-03.wav"
    with application.primary_context.capture() as transcript:
        await instrument.parameters["buffer_id"].set_(path)
    assert len(transcript.sent_messages) == 1
    _, message = transcript.sent_messages[0]
    assert message.to_list() == [
        None,
        [["/b_allocRead", 0, str(locate(path)), 0, -1]],
    ]
    assert instrument.parameters["buffer_id"].buffer_proxy is not None
    assert instrument.parameters["buffer_id"].path is path


@pytest.mark.asyncio
async def test_perform(application):
    track = application.primary_context["Track"]
    instrument = await track.add_device(BasicSampler)
    with application.primary_context.capture() as transcript:
        # Buffer has not been allocated, so make no notes
        await instrument.perform([NoteOnMessage(pitch=60, velocity=100)])
    assert len(transcript.sent_messages) == 0
    await instrument.parameters["buffer_id"].set_("tloen:samples/808/bd-long-03.wav")
    with application.primary_context.capture() as transcript:
        await instrument.perform([NoteOnMessage(pitch=60, velocity=100)])
    assert len(transcript.sent_messages) == 1
    synthdef = instrument.synthdef.build()
    bundle_contents = [
        [
            "/s_new",
            synthdef.actual_name,
            1049,
            0,
            1046,
            "amplitude",
            0.62000124000248,
            "buffer_id",
            0.0,
            "out",
            28.0,
        ],
    ]
    assert transcript.sent_messages[0][1].to_list() == [
        None,
        [["/d_recv", synthdef.compile(), [None, bundle_contents]]],
    ]
