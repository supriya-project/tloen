import pytest

from tloen.domain import Application, RackDevice


@pytest.mark.asyncio
async def test_1():
    """
    Unbooted, move one chain before another
    """
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    rack_device = await track.add_device(RackDevice)
    chain_one = await rack_device.add_chain()
    chain_two = await rack_device.add_chain()
    await chain_two.move(rack_device, 0)
    assert list(rack_device.chains) == [chain_two, chain_one]


@pytest.mark.asyncio
async def test_2():
    """
    Booted, move one chain before another
    """
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    rack_device = await track.add_device(RackDevice)
    chain_one = await rack_device.add_chain()
    chain_two = await rack_device.add_chain()
    await application.boot()
    with context.provider.server.osc_protocol.capture() as transcript:
        await chain_two.move(rack_device, 0)
    assert list(rack_device.chains) == [chain_two, chain_one]
    assert len(transcript.sent_messages) == 1
    _, message = transcript.sent_messages[0]
    assert message.to_list() == [None, [["/g_head", 1017, 1032]]]


@pytest.mark.asyncio
async def test_3():
    """
    Booted, with cross-referencing sends, move one chain before another
    """
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    rack_device = await track.add_device(RackDevice)
    chain_one = await rack_device.add_chain()
    chain_two = await rack_device.add_chain()
    await chain_one.add_send(chain_two)
    await chain_two.add_send(chain_one)
    await application.boot()
    with context.provider.server.osc_protocol.capture() as transcript:
        await chain_two.move(rack_device, 0)
    assert len(transcript.sent_messages) == 1
    _, message = transcript.sent_messages[0]
    assert message.to_list() == [
        None,
        [
            [
                "/s_new",
                "mixer/patch[gain]/2x2",
                1078,
                0,
                1044,
                "in_",
                28.0,
                "out",
                24.0,
            ],
            [
                "/s_new",
                "mixer/patch[fb,gain]/2x2",
                1079,
                0,
                1030,
                "in_",
                24.0,
                "out",
                26.0,
            ],
            ["/g_head", 1017, 1032],
            ["/n_set", 1046, "gate", 0],
            ["/n_set", 1047, "gate", 0],
        ],
    ]


@pytest.mark.asyncio
async def test_4():
    """
    Booted, move one chain from one rack device to another
    """
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    rack_device_one = await track.add_device(RackDevice)
    rack_device_two = await track.add_device(RackDevice)
    chain = await rack_device_one.add_chain()
    await application.boot()
    with context.provider.server.osc_protocol.capture() as transcript:
        await chain.move(rack_device_two, 0)
    assert len(transcript.sent_messages) == 1
    _, message = transcript.sent_messages[0]
    assert message.to_list() == [
        None,
        [
            [
                "/s_new",
                "mixer/patch[gain]/2x2",
                1066,
                0,
                1030,
                "in_",
                24.0,
                "out",
                26.0,
            ],
            ["/g_tail", 1035, 1018],
            ["/n_set", 1031, "gate", 0],
        ],
    ]
