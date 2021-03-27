import asyncio

import pytest
from supriya import scsynth
from supriya.osc import find_free_port
from supriya.providers import Provider
from supriya.realtime.servers import AsyncServer

from tloen.domain import Chain


@pytest.fixture(scope="module")
def event_loop():
    """Change event_loop fixture to module level."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="module")
def shutdown_scsynth():
    scsynth.kill()
    yield
    scsynth.kill()


@pytest.fixture(autouse=True, scope="module")
async def shutdown_async_servers(shutdown_scsynth, event_loop):
    for server in tuple(AsyncServer._servers):
        await server._shutdown()
    yield
    for server in tuple(AsyncServer._servers):
        await server._shutdown()


@pytest.fixture(autouse=True, scope="module")
async def provider(shutdown_async_servers, event_loop):
    yield await Provider.realtime_async(port=find_free_port())


@pytest.fixture
async def reset_provider(provider, event_loop):
    yield provider
    await provider.server.reset()


@pytest.mark.parametrize(
    "chain_names, levels",
    [
        (["outer/a/a"], [0, 1, 1, 1, 1, 1, 1, 1]),
        (["outer/a/b"], [1, 0, 0, 0, 1, 1, 1, 1]),
        (["inner/a/a"], [1, 1, 0, 1, 1, 1, 1, 1]),
        (["inner/a/b"], [1, 1, 1, 0, 1, 1, 1, 1]),
        (["outer/b/a"], [1, 1, 1, 1, 0, 1, 1, 1]),
        (["outer/b/b"], [1, 1, 1, 1, 1, 0, 0, 0]),
        (["inner/b/a"], [1, 1, 1, 1, 1, 1, 0, 1]),
        (["inner/b/b"], [1, 1, 1, 1, 1, 1, 1, 0]),
    ],
)
@pytest.mark.asyncio
async def test_levels_nested(
    reset_provider, chain_mute_solo_application, chain_names, levels
):
    await chain_mute_solo_application.boot(provider=reset_provider)
    for chain_name in chain_names:
        chain = chain_mute_solo_application.primary_context[chain_name]
        await chain.mute()
    await asyncio.sleep(0.2)
    assert [
        int(_)
        for _ in chain_mute_solo_application.primary_context.master_track.rms_levels[
            "input"
        ]
    ] == levels


@pytest.mark.parametrize(
    "chain_names",
    [
        ["outer/a/a"],
        ["outer/a/b"],
        ["inner/a/a"],
        ["inner/a/b"],
        ["outer/b/a"],
        ["outer/b/b"],
        ["inner/b/a"],
        ["inner/b/b"],
    ],
)
@pytest.mark.asyncio
async def test_transcript(reset_provider, chain_mute_solo_application, chain_names):
    await chain_mute_solo_application.boot(provider=reset_provider)
    context = chain_mute_solo_application.primary_context
    for chain_name in chain_names:
        chain = context[chain_name]
        with context.provider.server.osc_protocol.capture() as transcript:
            await chain.mute()
        assert len(transcript.sent_messages) == 1
        _, message = transcript.sent_messages[0]
        assert message.to_list() == [
            None,
            [["/n_set", chain.node_proxies["output"].identifier, "active", 0]],
        ]


@pytest.mark.parametrize("booted", [True, False])
@pytest.mark.parametrize(
    "chain_names, expected",
    [
        (["outer/a/a"], [0, 1, 1, 1, 1, 1, 1, 1]),
        (["outer/a/b"], [1, 0, 1, 1, 1, 1, 1, 1]),
        (["inner/a/a"], [1, 1, 0, 1, 1, 1, 1, 1]),
        (["inner/a/b"], [1, 1, 1, 0, 1, 1, 1, 1]),
        (["outer/b/a"], [1, 1, 1, 1, 0, 1, 1, 1]),
        (["outer/b/b"], [1, 1, 1, 1, 1, 0, 1, 1]),
        (["inner/b/a"], [1, 1, 1, 1, 1, 1, 0, 1]),
        (["inner/b/b"], [1, 1, 1, 1, 1, 1, 1, 0]),
    ],
)
@pytest.mark.asyncio
async def test_is_active(
    reset_provider, chain_mute_solo_application, booted, chain_names, expected
):
    if booted:
        await chain_mute_solo_application.boot(provider=reset_provider)
    for chain_name in chain_names:
        chain = chain_mute_solo_application.primary_context[chain_name]
        await chain.mute()
    all_chains = list(
        chain_mute_solo_application.primary_context.depth_first(prototype=Chain)
    )
    actual = [bool(chain.is_active) for chain in all_chains]
    assert actual == [bool(x) for x in expected]


@pytest.mark.parametrize("booted", [True, False])
@pytest.mark.parametrize(
    "chain_names, expected",
    [
        (["outer/a/a"], [1, 0, 0, 0, 0, 0, 0, 0]),
        (["outer/a/b"], [0, 1, 0, 0, 0, 0, 0, 0]),
        (["inner/a/a"], [0, 0, 1, 0, 0, 0, 0, 0]),
        (["inner/a/b"], [0, 0, 0, 1, 0, 0, 0, 0]),
        (["outer/b/a"], [0, 0, 0, 0, 1, 0, 0, 0]),
        (["outer/b/b"], [0, 0, 0, 0, 0, 1, 0, 0]),
        (["inner/b/a"], [0, 0, 0, 0, 0, 0, 1, 0]),
        (["inner/b/b"], [0, 0, 0, 0, 0, 0, 0, 1]),
    ],
)
@pytest.mark.asyncio
async def test_is_muted(
    reset_provider, chain_mute_solo_application, booted, chain_names, expected
):
    if booted:
        await chain_mute_solo_application.boot(provider=reset_provider)
    for chain_name in chain_names:
        chain = chain_mute_solo_application.primary_context[chain_name]
        await chain.mute()
    all_chains = list(
        chain_mute_solo_application.primary_context.depth_first(prototype=Chain)
    )
    actual = [bool(chain.is_muted) for chain in all_chains]
    assert actual == [bool(x) for x in expected]


@pytest.mark.asyncio
async def test_repeat(chain_mute_solo_application):
    await chain_mute_solo_application.boot()
    await chain_mute_solo_application.primary_context["outer/a/a"].mute()
    with chain_mute_solo_application.primary_context.provider.server.osc_protocol.capture() as transcript:
        await chain_mute_solo_application.primary_context["outer/a/a"].mute()
    assert not len(transcript.sent_messages)
