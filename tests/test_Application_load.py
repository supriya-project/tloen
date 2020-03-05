import pytest
import yaml

from tloen.domain import (
    Application,
    Arpeggiator,
    BasicSampler,
    RackDevice,
    Transfer,
)


@pytest.mark.asyncio
async def test(tmp_path):
    app_one = Application()
    context = await app_one.add_context()
    track_one = await context.add_track(name="One")
    track_two = await context.add_track(name="Two")
    await track_one.add_send(track_two)
    await track_one.solo(exclusive=False)
    await track_two.add_send(track_one)
    await track_two.solo(exclusive=False)
    await track_two.mute()
    await track_two.cue()
    rack = await track_one.add_device(RackDevice, channel_count=4)
    chain = await rack.add_chain(transfer=Transfer(in_pitch=64, out_pitch=60))
    await chain.parameters["gain"].set_(-6.0)
    await chain.add_device(Arpeggiator)
    sampler = await chain.add_device(BasicSampler)
    await sampler.parameters["active"].set_(False)
    await sampler.parameters["buffer_id"].set_("tloen:samples/808/bd-long-03.wav")
    file_path = tmp_path / "application.yaml"
    assert not file_path.exists()
    app_one.save(file_path)
    assert file_path.exists()
    app_two = await Application.load(file_path)
    assert app_one is not app_two
    assert yaml.dump(app_one.serialize()) == yaml.dump(app_two.serialize())
