import pytest

from tloen.core import Application, RackDevice


@pytest.mark.asyncio
async def test_1():
    """
    Remove one chain
    """
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    rack_device = await track.add_device(RackDevice)
    chain = await rack_device.add_chain()
    await rack_device.remove_chains(chain)
    assert list(rack_device.chains) == []
    assert chain.application is None
    assert chain.graph_order == ()
    assert chain.parent is None
    assert chain.provider is None


@pytest.mark.asyncio
async def test_2():
    """
    Remove two chains
    """
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    rack_device = await track.add_device(RackDevice)
    chain_one = await rack_device.add_chain()
    chain_two = await rack_device.add_chain()
    await rack_device.remove_chains(chain_one, chain_two)
    assert list(rack_device.chains) == []
    assert chain_one.application is None
    assert chain_one.graph_order == ()
    assert chain_one.parent is None
    assert chain_one.provider is None
    assert chain_two.application is None
    assert chain_two.graph_order == ()
    assert chain_two.parent is None
    assert chain_two.provider is None


@pytest.mark.asyncio
async def test_3():
    """
    Remove first chain, leaving second untouched
    """
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    rack_device = await track.add_device(RackDevice)
    chain_one = await rack_device.add_chain()
    chain_two = await rack_device.add_chain()
    await rack_device.remove_chains(chain_one)
    assert list(rack_device.chains) == [chain_two]
    assert chain_one.application is None
    assert chain_one.graph_order == ()
    assert chain_one.parent is None
    assert chain_one.provider is None
    assert chain_two.application is context.application
    assert chain_two.graph_order == (3, 0, 0, 0, 5, 0, 0, 0)
    assert chain_two.parent is rack_device.chains
    assert chain_two.provider is None


@pytest.mark.asyncio
async def test_4():
    """
    Boot, remove first chain, leaving second untouched
    """
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    rack_device = await track.add_device(RackDevice)
    chain_one = await rack_device.add_chain()
    chain_two = await rack_device.add_chain()
    await application.boot()
    await rack_device.remove_chains(chain_one)
    assert context.provider is not None
    assert list(rack_device.chains) == [chain_two]
    assert chain_one.application is None
    assert chain_one.graph_order == ()
    assert chain_one.parent is None
    assert chain_one.provider is None
    assert chain_two.application is context.application
    assert chain_two.graph_order == (3, 0, 0, 0, 5, 0, 0, 0)
    assert chain_two.parent is rack_device.chains
    assert chain_two.provider is context.provider
