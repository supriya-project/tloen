import pytest
import yaml
from uqbar.strings import normalize

from tloen.domain import Application, Arpeggiator, BasicSampler, RackDevice


@pytest.mark.asyncio
async def test_1():
    app = Application()
    context = await app.add_context()
    cue_track, master_track = context.cue_track, context.master_track
    track_one = await context.add_track(name="One")
    track_two = await context.add_track(name="Two")
    await track_one.add_send(track_two)
    await track_one.solo(exclusive=False)
    await track_two.add_send(track_one)
    await track_two.solo(exclusive=False)
    await track_two.mute()
    await track_two.cue()
    rack = await track_one.add_device(RackDevice, channel_count=4)
    chain = await rack.add_chain()
    await chain.parameters["gain"].set_(-6.0)
    arpeggiator = await chain.add_device(Arpeggiator)
    sampler = await chain.add_device(BasicSampler)
    await sampler.parameters["active"].set_(False)
    await sampler.parameters["buffer_id"].set_("tloen:samples/808/bd-long-03.wav")
    assert normalize(yaml.dump(app.serialize())) == normalize(
        f"""
        entities:
        - kind: Application
          spec:
            channel_count: 2
            contexts:
            - {context.uuid}
            transport:
              kind: Transport
              spec:
                tempo: 120.0
                time_signature:
                - 4
                - 4
        - kind: Context
          meta:
            uuid: {context.uuid}
          spec:
            cue_track: {cue_track.uuid}
            master_track: {master_track.uuid}
            tracks:
            - {track_one.uuid}
            - {track_two.uuid}
        - kind: CueTrack
          meta:
            uuid: {cue_track.uuid}
          spec:
            channel_count: 2
            parameters:
            - {cue_track.parameters["gain"].uuid}
            - {cue_track.parameters["mix"].uuid}
            sends:
            - {cue_track.postfader_sends[0].uuid}
        - kind: BusParameter
          meta:
            name: gain
            uuid: {cue_track.parameters["gain"].uuid}
          spec:
            value: 0.0
        - kind: BusParameter
          meta:
            name: mix
            uuid: {cue_track.parameters["mix"].uuid}
          spec:
            value: 0.0
        - kind: DirectOut
          meta:
            uuid: {cue_track.postfader_sends[0].uuid}
          spec:
            position: postfader
            target_bus_id: 2
            target_channel_count: 2
        - kind: MasterTrack
          meta:
            uuid: {master_track.uuid}
          spec:
            parameters:
            - {master_track.parameters["gain"].uuid}
            sends:
            - {master_track.postfader_sends[0].uuid}
        - kind: BusParameter
          meta:
            name: gain
            uuid: {master_track.parameters["gain"].uuid}
          spec:
            value: 0.0
        - kind: DirectOut
          meta:
            uuid: {master_track.postfader_sends[0].uuid}
          spec:
            position: postfader
            target_bus_id: 0
            target_channel_count: 2
        - kind: Track
          meta:
            name: One
            uuid: {track_one.uuid}
          spec:
            devices:
            - {rack.uuid}
            is_soloed: true
            parameters:
            - {track_one.parameters["gain"].uuid}
            - {track_one.parameters["panning"].uuid}
            sends:
            - {track_one.postfader_sends[0].uuid}
            - {track_one.postfader_sends[1].uuid}
        - kind: BusParameter
          meta:
            name: gain
            uuid: {track_one.parameters["gain"].uuid}
          spec:
            value: 0.0
        - kind: BusParameter
          meta:
            name: panning
            uuid: {track_one.parameters["panning"].uuid}
          spec:
            value: 0.0
        - kind: Send
          meta:
            uuid: {track_one.postfader_sends[0].uuid}
          spec:
            position: postfader
            target: default
        - kind: Send
          meta:
            uuid: {track_one.postfader_sends[1].uuid}
          spec:
            position: postfader
            target: {track_two.uuid}
        - kind: RackDevice
          meta:
            uuid: {rack.uuid}
          spec:
            chains:
            - {chain.uuid}
            channel_count: 4
            parameters:
            - {rack.parameters["active"].uuid}
        - kind: CallbackParameter
          meta:
            name: active
            uuid: {rack.parameters["active"].uuid}
          spec:
            value: true
        - kind: Chain
          meta:
            uuid: {chain.uuid}
          spec:
            devices:
            - {arpeggiator.uuid}
            - {sampler.uuid}
            parameters:
            - {chain.parameters["gain"].uuid}
            - {chain.parameters["panning"].uuid}
            sends:
            - {chain.postfader_sends[0].uuid}
            transfer:
              kind: Transfer
        - kind: BusParameter
          meta:
            name: gain
            uuid: {chain.parameters["gain"].uuid}
          spec:
            value: -6.0
        - kind: BusParameter
          meta:
            name: panning
            uuid: {chain.parameters["panning"].uuid}
          spec:
            value: 0.0
        - kind: Send
          meta:
            uuid: {chain.postfader_sends[0].uuid}
          spec:
            position: postfader
            target: default
        - kind: Arpeggiator
          meta:
            uuid: {arpeggiator.uuid}
          spec:
            parameters:
            - {arpeggiator.parameters["active"].uuid}
        - kind: CallbackParameter
          meta:
            name: active
            uuid: {arpeggiator.parameters["active"].uuid}
          spec:
            value: true
        - kind: BasicSampler
          meta:
            uuid: {sampler.uuid}
          spec:
            parameters:
            - {sampler.parameters["buffer_id"].uuid}
            - {sampler.parameters["active"].uuid}
        - kind: BufferParameter
          meta:
            name: buffer_id
            uuid: {sampler.parameters["buffer_id"].uuid}
          spec:
            path: tloen:samples/808/bd-long-03.wav
        - kind: CallbackParameter
          meta:
            name: active
            uuid: {sampler.parameters["active"].uuid}
          spec:
            value: false
        - kind: Track
          meta:
            name: Two
            uuid: {track_two.uuid}
          spec:
            is_muted: true
            is_soloed: true
            parameters:
            - {track_two.parameters["gain"].uuid}
            - {track_two.parameters["panning"].uuid}
            sends:
            - {track_two.postfader_sends[0].uuid}
            - {track_two.postfader_sends[1].uuid}
        - kind: BusParameter
          meta:
            name: gain
            uuid: {track_two.parameters["gain"].uuid}
          spec:
            value: 0.0
        - kind: BusParameter
          meta:
            name: panning
            uuid: {track_two.parameters["panning"].uuid}
          spec:
            value: 0.0
        - kind: Send
          meta:
            uuid: {track_two.postfader_sends[0].uuid}
          spec:
            position: postfader
            target: default
        - kind: Send
          meta:
            uuid: {track_two.postfader_sends[1].uuid}
          spec:
            position: postfader
            target: {track_one.uuid}
        """
    )
