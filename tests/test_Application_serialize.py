import pytest
import yaml
from uqbar.strings import normalize

from tloen.domain import Application, Arpeggiator, Instrument, RackDevice


@pytest.mark.asyncio
async def test_1():
    app = Application()
    context = await app.add_context()
    cue_track, master_track = context.cue_track, context.master_track
    track = await context.add_track()
    rack = await track.add_device(RackDevice, channel_count=4)
    chain = await rack.add_chain()
    await chain.parameters["gain"].set_(-6.0)
    arpeggiator = await chain.add_device(Arpeggiator)
    instrument = await chain.add_device(Instrument)
    await instrument.parameters["active"].set_(False)
    assert normalize(yaml.dump(app.serialize())) == normalize(
        f"""
        kind: Application
        spec:
          channel_count: 2
          contexts:
          - kind: Context
            meta:
              uuid: {context.uuid}
            spec:
              cue_track:
                kind: CueTrack
                meta:
                  uuid: {cue_track.uuid}
                spec:
                  channel_count: 2
                  parameters:
                  - kind: CallbackParameter
                    meta:
                      name: active
                      uuid: {cue_track.parameters["active"].uuid}
                    spec:
                      value: true
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
                  sends:
                  - kind: DirectOut
                    meta:
                      uuid: {cue_track.postfader_sends[0].uuid}
                    spec:
                      position: postfader
                      target_bus_id: 2
                      target_channel_count: 2
              master_track:
                kind: MasterTrack
                meta:
                  uuid: {master_track.uuid}
                spec:
                  parameters:
                  - kind: CallbackParameter
                    meta:
                      name: active
                      uuid: {master_track.parameters["active"].uuid}
                    spec:
                      value: true
                  - kind: BusParameter
                    meta:
                      name: gain
                      uuid: {master_track.parameters["gain"].uuid}
                    spec:
                      value: 0.0
                  sends:
                  - kind: DirectOut
                    meta:
                      uuid: {master_track.postfader_sends[0].uuid}
                    spec:
                      position: postfader
                      target_bus_id: 0
                      target_channel_count: 2
              tracks:
              - kind: Track
                meta:
                  uuid: {track.uuid}
                spec:
                  devices:
                  - kind: RackDevice
                    meta:
                      uuid: {rack.uuid}
                    spec:
                      chains:
                      - kind: Chain
                        meta:
                          uuid: {chain.uuid}
                        spec:
                          devices:
                          - kind: Arpeggiator
                            meta:
                              uuid: {arpeggiator.uuid}
                            spec:
                              parameters:
                              - kind: CallbackParameter
                                meta:
                                  name: active
                                  uuid: {arpeggiator.parameters["active"].uuid}
                                spec:
                                  value: true
                          - kind: Instrument
                            meta:
                              uuid: {instrument.uuid}
                            spec:
                              parameters:
                              - kind: CallbackParameter
                                meta:
                                  name: active
                                  uuid: {instrument.parameters["active"].uuid}
                                spec:
                                  value: false
                          parameters:
                          - kind: CallbackParameter
                            meta:
                              name: active
                              uuid: {chain.parameters["active"].uuid}
                            spec:
                              value: true
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
                          sends:
                          - kind: Send
                            meta:
                              uuid: {chain.postfader_sends[0].uuid}
                            spec:
                              position: postfader
                              target: default
                      channel_count: 4
                      parameters:
                      - kind: CallbackParameter
                        meta:
                          name: active
                          uuid: {rack.parameters["active"].uuid}
                        spec:
                          value: true
                  parameters:
                  - kind: CallbackParameter
                    meta:
                      name: active
                      uuid: {track.parameters["active"].uuid}
                    spec:
                      value: true
                  - kind: BusParameter
                    meta:
                      name: gain
                      uuid: {track.parameters["gain"].uuid}
                    spec:
                      value: 0.0
                  - kind: BusParameter
                    meta:
                      name: panning
                      uuid: {track.parameters["panning"].uuid}
                    spec:
                      value: 0.0
                  sends:
                  - kind: Send
                    meta:
                      uuid: {track.postfader_sends[0].uuid}
                    spec:
                      position: postfader
                      target: default
          transport:
            kind: Transport
            spec:
              tempo: 120.0
              time_signature:
              - 4
              - 4
        """
    )
