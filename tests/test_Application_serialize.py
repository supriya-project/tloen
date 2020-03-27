import pytest
import yaml
from uqbar.strings import normalize


@pytest.mark.asyncio
async def test_1(serialization_application):
    app = serialization_application
    scene = app.scenes[0]
    context = app.contexts[0]
    cue_track = context.cue_track
    master_track = context.master_track
    track_one, track_two = context.tracks
    rack = track_one.devices[0]
    chain = rack.chains[0]
    arpeggiator, sampler = chain.devices
    assert normalize(yaml.dump(app.serialize())) == normalize(
        f"""
        entities:
        - kind: Application
          spec:
            channel_count: 2
            contexts:
            - {context.uuid}
            scenes:
            - {scene.uuid}
            transport:
              kind: Transport
              spec:
                tempo: 120.0
                time_signature:
                - 4
                - 4
        - kind: Scene
          meta:
            uuid: {scene.uuid}
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
            parent: {context.uuid}
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
            parent: {cue_track.uuid}
            uuid: {cue_track.parameters["gain"].uuid}
          spec:
            value: 0.0
        - kind: BusParameter
          meta:
            name: mix
            parent: {cue_track.uuid}
            uuid: {cue_track.parameters["mix"].uuid}
          spec:
            value: 0.0
        - kind: DirectOut
          meta:
            parent: {cue_track.uuid}
            uuid: {cue_track.postfader_sends[0].uuid}
          spec:
            position: postfader
            target_bus_id: 2
            target_channel_count: 2
        - kind: MasterTrack
          meta:
            parent: {context.uuid}
            uuid: {master_track.uuid}
          spec:
            parameters:
            - {master_track.parameters["gain"].uuid}
            sends:
            - {master_track.postfader_sends[0].uuid}
        - kind: BusParameter
          meta:
            name: gain
            parent: {master_track.uuid}
            uuid: {master_track.parameters["gain"].uuid}
          spec:
            value: 0.0
        - kind: DirectOut
          meta:
            parent: {master_track.uuid}
            uuid: {master_track.postfader_sends[0].uuid}
          spec:
            position: postfader
            target_bus_id: 0
            target_channel_count: 2
        - kind: Track
          meta:
            name: One
            parent: {context.uuid}
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
            slots:
            - {track_one.slots[0].uuid}
        - kind: BusParameter
          meta:
            name: gain
            parent: {track_one.uuid}
            uuid: {track_one.parameters["gain"].uuid}
          spec:
            value: 0.0
        - kind: BusParameter
          meta:
            name: panning
            parent: {track_one.uuid}
            uuid: {track_one.parameters["panning"].uuid}
          spec:
            value: 0.0
        - kind: Send
          meta:
            parent: {track_one.uuid}
            uuid: {track_one.postfader_sends[0].uuid}
          spec:
            position: postfader
            target: default
        - kind: Send
          meta:
            parent: {track_one.uuid}
            uuid: {track_one.postfader_sends[1].uuid}
          spec:
            position: postfader
            target: {track_two.uuid}
        - kind: RackDevice
          meta:
            parent: {track_one.uuid}
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
            parent: {rack.uuid}
            uuid: {rack.parameters["active"].uuid}
          spec:
            value: true
        - kind: Chain
          meta:
            parent: {rack.uuid}
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
              spec:
                in_pitch: 64
                out_pitch: 60
        - kind: BusParameter
          meta:
            name: gain
            parent: {chain.uuid}
            uuid: {chain.parameters["gain"].uuid}
          spec:
            value: -6.0
        - kind: BusParameter
          meta:
            name: panning
            parent: {chain.uuid}
            uuid: {chain.parameters["panning"].uuid}
          spec:
            value: 0.0
        - kind: Send
          meta:
            parent: {chain.uuid}
            uuid: {chain.postfader_sends[0].uuid}
          spec:
            position: postfader
            target: default
        - kind: Arpeggiator
          meta:
            parent: {chain.uuid}
            uuid: {arpeggiator.uuid}
          spec:
            parameters:
            - {arpeggiator.parameters["active"].uuid}
        - kind: CallbackParameter
          meta:
            name: active
            parent: {arpeggiator.uuid}
            uuid: {arpeggiator.parameters["active"].uuid}
          spec:
            value: true
        - kind: BasicSampler
          meta:
            parent: {chain.uuid}
            uuid: {sampler.uuid}
          spec:
            parameters:
            - {sampler.parameters["active"].uuid}
            - {sampler.parameters["buffer_id"].uuid}
        - kind: CallbackParameter
          meta:
            name: active
            parent: {sampler.uuid}
            uuid: {sampler.parameters["active"].uuid}
          spec:
            value: false
        - kind: BufferParameter
          meta:
            name: buffer_id
            parent: {sampler.uuid}
            uuid: {sampler.parameters["buffer_id"].uuid}
          spec:
            path: tloen:samples/808/bd-long-03.wav
        - kind: Slot
          meta:
            parent: {track_one.uuid}
            uuid: {track_one.slots[0].uuid}
          spec:
            clip: {track_one.slots[0].clip.uuid}
        - kind: Clip
          meta:
            parent: {track_one.slots[0].uuid}
            uuid: {track_one.slots[0].clip.uuid}
          spec:
            notes:
            - pitch: 60
              start_offset: 0
              stop_offset: 0.25
              velocity: 100.0
        - kind: Track
          meta:
            name: Two
            parent: {context.uuid}
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
            slots:
            - {track_two.slots[0].uuid}
        - kind: BusParameter
          meta:
            name: gain
            parent: {track_two.uuid}
            uuid: {track_two.parameters["gain"].uuid}
          spec:
            value: 0.0
        - kind: BusParameter
          meta:
            name: panning
            parent: {track_two.uuid}
            uuid: {track_two.parameters["panning"].uuid}
          spec:
            value: 0.0
        - kind: Send
          meta:
            parent: {track_two.uuid}
            uuid: {track_two.postfader_sends[0].uuid}
          spec:
            position: postfader
            target: default
        - kind: Send
          meta:
            parent: {track_two.uuid}
            uuid: {track_two.postfader_sends[1].uuid}
          spec:
            position: postfader
            target: {track_one.uuid}
        - kind: Slot
          meta:
            parent: {track_two.uuid}
            uuid: {track_two.slots[0].uuid}
        """
    )
